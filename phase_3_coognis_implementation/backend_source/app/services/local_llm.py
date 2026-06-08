from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AppSetting

SUPPORTED_LLM_PROVIDERS = {"mock", "llama_cpp", "openai"}
OPENAI_MODEL_OPTIONS = ("gpt-5.4-mini", "gpt-5.4")
LLAMA_CPP_DEFAULT_MODEL = "local-default"
MOCK_DEFAULT_MODEL = "mock"


class LlmClient:
    backend_name = "base"
    model_name = "base"

    def generate(self, prompt: str) -> str:
        raise NotImplementedError


LocalLlmClient = LlmClient


class MockLocalLlmClient(LlmClient):
    backend_name = "mock"
    model_name = MOCK_DEFAULT_MODEL

    def generate(self, prompt: str) -> str:
        return f"Mock local LLM output based on prompt:\n\n{prompt}"


class LlamaCppLocalLlmClient(LlmClient):
    backend_name = "llama_cpp"

    def __init__(
        self,
        *,
        model_name: str,
        model_path: str,
        n_ctx: int,
        max_tokens: int,
        temperature: float,
        n_threads: int,
    ) -> None:
        model_file = Path(model_path)
        if not model_file.exists() or not model_file.is_file():
            raise RuntimeError(
                f"LOCAL_LLM_MODEL_PATH does not point to a readable GGUF model file: {model_path}"
            )

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "The 'llama_cpp' LLM provider is selected but llama_cpp is not installed."
            ) from exc

        self.model_name = model_name
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=False,
        )

    def generate(self, prompt: str) -> str:
        response = self._model.create_completion(
            prompt=prompt,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        choices = response.get("choices") or []
        if not choices:
            return ""
        return str((choices[0] or {}).get("text") or "").strip()


class OpenAiLlmClient(LlmClient):
    backend_name = "openai"

    def __init__(
        self,
        *,
        model_name: str,
        api_key: str,
        project: str | None,
        organization: str | None,
        max_output_tokens: int,
        temperature: float,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The 'openai' LLM provider is selected but the openai package is not installed."
            ) from exc

        if not api_key:
            raise RuntimeError(
                "The 'openai' LLM provider is selected but OPENAI_API_KEY is not configured."
            )

        self.model_name = model_name
        self._max_output_tokens = max_output_tokens
        self._temperature = temperature
        self._client = OpenAI(
            api_key=api_key,
            project=project,
            organization=organization,
        )

    def generate(self, prompt: str) -> str:
        response = self._client.responses.create(
            model=self.model_name,
            input=prompt,
            max_output_tokens=self._max_output_tokens,
            temperature=self._temperature,
        )
        output_text = getattr(response, "output_text", None)
        if output_text:
            return str(output_text).strip()
        return ""


@dataclass(frozen=True)
class LlmRuntimeSelection:
    provider: str
    model: str


@dataclass(frozen=True)
class LlmProviderOption:
    provider: str
    default_model: str
    model_options: tuple[str, ...]


def get_supported_llm_options() -> tuple[LlmProviderOption, ...]:
    return (
        LlmProviderOption(
            provider="openai",
            default_model=OPENAI_MODEL_OPTIONS[0],
            model_options=OPENAI_MODEL_OPTIONS,
        ),
        LlmProviderOption(
            provider="llama_cpp",
            default_model=LLAMA_CPP_DEFAULT_MODEL,
            model_options=(LLAMA_CPP_DEFAULT_MODEL,),
        ),
        LlmProviderOption(
            provider="mock",
            default_model=MOCK_DEFAULT_MODEL,
            model_options=(MOCK_DEFAULT_MODEL,),
        ),
    )


def normalize_llm_selection(provider: str | None, model: str | None) -> LlmRuntimeSelection:
    normalized_provider = (provider or settings.llm_provider or settings.local_llm_backend).strip().lower()
    if normalized_provider not in SUPPORTED_LLM_PROVIDERS:
        raise ValueError(
            f"Unsupported LLM provider '{provider}'. Expected one of: {', '.join(sorted(SUPPORTED_LLM_PROVIDERS))}."
        )

    normalized_model = (model or "").strip()
    if normalized_provider == "openai":
        normalized_model = normalized_model or settings.llm_model or OPENAI_MODEL_OPTIONS[0]
        if normalized_model not in OPENAI_MODEL_OPTIONS:
            raise ValueError(
                f"Unsupported OpenAI model '{normalized_model}'. Expected one of: {', '.join(OPENAI_MODEL_OPTIONS)}."
            )
        return LlmRuntimeSelection(provider=normalized_provider, model=normalized_model)

    if normalized_provider == "llama_cpp":
        normalized_model = normalized_model or settings.llm_model or LLAMA_CPP_DEFAULT_MODEL
        if normalized_model != LLAMA_CPP_DEFAULT_MODEL:
            raise ValueError(
                f"Unsupported llama_cpp model '{normalized_model}'. Expected '{LLAMA_CPP_DEFAULT_MODEL}'."
            )
        return LlmRuntimeSelection(provider=normalized_provider, model=normalized_model)

    normalized_model = normalized_model or settings.llm_model or MOCK_DEFAULT_MODEL
    if normalized_model != MOCK_DEFAULT_MODEL:
        raise ValueError(f"Unsupported mock model '{normalized_model}'. Expected '{MOCK_DEFAULT_MODEL}'.")
    return LlmRuntimeSelection(provider=normalized_provider, model=normalized_model)


def get_env_llm_selection() -> LlmRuntimeSelection:
    return normalize_llm_selection(settings.llm_provider, settings.llm_model)


def get_db_llm_selection(db: Session | None) -> LlmRuntimeSelection:
    if db is None:
        return get_env_llm_selection()

    rows = db.execute(
        select(AppSetting).where(AppSetting.key.in_(("llm.provider", "llm.model")))
    ).scalars().all()
    values = {row.key: row.value for row in rows}
    provider = values.get("llm.provider", settings.llm_provider)
    model = values.get("llm.model", settings.llm_model)
    return normalize_llm_selection(provider, model)


@lru_cache(maxsize=8)
def _build_llm_client(provider: str, model: str) -> LlmClient:
    if provider == "openai":
        return OpenAiLlmClient(
            model_name=model,
            api_key=settings.openai_api_key or "",
            project=settings.openai_project,
            organization=settings.openai_org_id,
            max_output_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
        )

    if provider == "llama_cpp":
        return LlamaCppLocalLlmClient(
            model_name=model,
            model_path=settings.local_llm_model_path,
            n_ctx=settings.local_llm_context_window,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            n_threads=settings.local_llm_threads,
        )

    return MockLocalLlmClient()


def get_llm_client_for_selection(selection: LlmRuntimeSelection) -> LlmClient:
    return _build_llm_client(selection.provider, selection.model)


def get_llm_client_from_db(db: Session | None) -> LlmClient:
    selection = get_db_llm_selection(db)
    return get_llm_client_for_selection(selection)


@lru_cache
def get_local_llm_client() -> LlmClient:
    return get_llm_client_for_selection(get_env_llm_selection())


def validate_llm_runtime() -> dict[str, str]:
    selection = get_env_llm_selection()
    details = {
        "backend": selection.provider,
        "provider": selection.provider,
        "model": selection.model,
    }

    if selection.provider == "mock":
        details["status"] = "ready"
        details["mode"] = "placeholder"
        return details

    if selection.provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("LLM_PROVIDER is set to 'openai' but OPENAI_API_KEY is not configured.")
        try:
            import openai  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "LLM_PROVIDER is set to 'openai' but the openai package is not installed."
            ) from exc
        details["status"] = "ready"
        details["mode"] = "runtime"
        return details

    model_file = Path(settings.local_llm_model_path)
    if not model_file.exists() or not model_file.is_file():
        raise RuntimeError(
            f"LOCAL_LLM_MODEL_PATH does not point to an existing GGUF file: {settings.local_llm_model_path}"
        )

    try:
        import llama_cpp  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "LLM_PROVIDER is set to 'llama_cpp' but llama_cpp is not installed in this environment."
        ) from exc

    details["status"] = "ready"
    details["mode"] = "runtime"
    details["model_path"] = str(model_file)
    return details


def validate_local_llm_runtime() -> dict[str, str]:
    return validate_llm_runtime()
