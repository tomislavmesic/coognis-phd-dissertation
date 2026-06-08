from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="SYNEXIS API", alias="APP_NAME")
    app_public_name: str = Field(default="COOGNIS", alias="APP_PUBLIC_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api", alias="API_V1_PREFIX")
    synapse_model_dir: str = Field(
        default="./models/synapse",
        alias="SYNAPSE_MODEL_DIR",
    )
    synapse_model_download_base_url: str | None = Field(
        default=None,
        alias="SYNAPSE_MODEL_DOWNLOAD_BASE_URL",
    )
    synapse_model_auto_download: bool = Field(
        default=False,
        alias="SYNAPSE_MODEL_AUTO_DOWNLOAD",
    )
    database_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    database_port: int = Field(default=5432, alias="POSTGRES_PORT")
    database_name: str = Field(default="synexis", alias="POSTGRES_DB")
    database_user: str = Field(default="postgres", alias="POSTGRES_USER")
    database_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    auth_session_secret: str = Field(default="change-me-in-production", alias="AUTH_SESSION_SECRET")
    auth_session_cookie_name: str = Field(default="synexis_session", alias="AUTH_SESSION_COOKIE_NAME")
    auth_session_same_site: str = Field(default="lax", alias="AUTH_SESSION_SAME_SITE")
    auth_session_https_only: bool = Field(default=False, alias="AUTH_SESSION_HTTPS_ONLY")
    auth_session_max_age_seconds: int = Field(default=43200, alias="AUTH_SESSION_MAX_AGE_SECONDS")
    auth_trusted_device_cookie_name: str = Field(
        default="coognis_trusted_device",
        alias="AUTH_TRUSTED_DEVICE_COOKIE_NAME",
    )
    auth_trusted_device_days_user: int = Field(default=14, alias="AUTH_TRUSTED_DEVICE_DAYS_USER")
    auth_trusted_device_days_expert: int = Field(default=14, alias="AUTH_TRUSTED_DEVICE_DAYS_EXPERT")
    auth_trusted_device_days_admin: int = Field(default=14, alias="AUTH_TRUSTED_DEVICE_DAYS_ADMIN")
    auth_allowed_origins_raw: str = Field(default="", alias="AUTH_ALLOWED_ORIGINS")
    auth_2fa_challenge_ttl_seconds: int = Field(default=300, alias="AUTH_2FA_CHALLENGE_TTL_SECONDS")
    auth_rate_limit_window_seconds: int = Field(default=300, alias="AUTH_RATE_LIMIT_WINDOW_SECONDS")
    auth_login_rate_limit_attempts: int = Field(default=8, alias="AUTH_LOGIN_RATE_LIMIT_ATTEMPTS")
    auth_2fa_rate_limit_attempts: int = Field(default=5, alias="AUTH_2FA_RATE_LIMIT_ATTEMPTS")
    auth_enforce_secure_defaults: bool = Field(default=True, alias="AUTH_ENFORCE_SECURE_DEFAULTS")
    auth_password_reset_ttl_seconds: int = Field(default=3600, alias="AUTH_PASSWORD_RESET_TTL_SECONDS")
    auth_password_reset_base_url: str | None = Field(default=None, alias="AUTH_PASSWORD_RESET_BASE_URL")
    email_delivery_mode: str = Field(default="log", alias="EMAIL_DELIVERY_MODE")
    email_from_address: str = Field(default="no-reply@synexis.local", alias="EMAIL_FROM_ADDRESS")
    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=False, alias="SMTP_USE_TLS")
    smtp_use_starttls: bool = Field(default=False, alias="SMTP_USE_STARTTLS")
    user_profile_min_interactions: int = Field(default=3, alias="USER_PROFILE_MIN_INTERACTIONS")
    user_profile_min_text_chars: int = Field(default=500, alias="USER_PROFILE_MIN_TEXT_CHARS")
    user_profile_refresh_every_interactions: int = Field(
        default=5,
        alias="USER_PROFILE_REFRESH_EVERY_INTERACTIONS",
    )
    user_profile_refresh_min_new_text_chars: int = Field(
        default=600,
        alias="USER_PROFILE_REFRESH_MIN_NEW_TEXT_CHARS",
    )
    user_profile_text_window_chars: int = Field(default=12000, alias="USER_PROFILE_TEXT_WINDOW_CHARS")
    expert_profile_min_interactions: int = Field(default=3, alias="EXPERT_PROFILE_MIN_INTERACTIONS")
    expert_profile_min_text_chars: int = Field(default=500, alias="EXPERT_PROFILE_MIN_TEXT_CHARS")
    expert_profile_refresh_every_interactions: int = Field(
        default=5,
        alias="EXPERT_PROFILE_REFRESH_EVERY_INTERACTIONS",
    )
    expert_profile_refresh_min_new_text_chars: int = Field(
        default=600,
        alias="EXPERT_PROFILE_REFRESH_MIN_NEW_TEXT_CHARS",
    )
    expert_profile_text_window_chars: int = Field(default=12000, alias="EXPERT_PROFILE_TEXT_WINDOW_CHARS")
    admin_allow_delete_closed_empty_chats: bool = Field(
        default=True,
        alias="ADMIN_ALLOW_DELETE_CLOSED_EMPTY_CHATS",
    )
    admin_open_empty_chat_delete_age_hours: int = Field(
        default=24,
        alias="ADMIN_OPEN_EMPTY_CHAT_DELETE_AGE_HOURS",
    )
    chat_typing_ttl_seconds: int = Field(default=10, alias="CHAT_TYPING_TTL_SECONDS")
    mind_enable_synapse: bool = Field(default=True, alias="MIND_ENABLE_SYNAPSE")
    mind_enable_uex: bool = Field(default=True, alias="MIND_ENABLE_UEX")
    mind_enable_ulm: bool = Field(default=False, alias="MIND_ENABLE_ULM")
    mind_enable_page: bool = Field(default=True, alias="MIND_ENABLE_PAGE")
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_model: str | None = Field(default=None, alias="LLM_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_project: str | None = Field(default=None, alias="OPENAI_PROJECT")
    openai_org_id: str | None = Field(default=None, alias="OPENAI_ORG_ID")
    local_llm_backend: str = Field(default="mock", alias="LOCAL_LLM_BACKEND")
    local_llm_model_path: str = Field(default="./models/llama/model.gguf", alias="LOCAL_LLM_MODEL_PATH")
    local_llm_context_window: int = Field(default=4096, alias="LOCAL_LLM_CONTEXT_WINDOW")
    llm_max_tokens: int = Field(
        default=512,
        alias="LLM_MAX_TOKENS",
        validation_alias=AliasChoices("LLM_MAX_TOKENS", "LOCAL_LLM_MAX_TOKENS"),
    )
    llm_temperature: float = Field(
        default=0.2,
        alias="LLM_TEMPERATURE",
        validation_alias=AliasChoices("LLM_TEMPERATURE", "LOCAL_LLM_TEMPERATURE"),
    )
    local_llm_threads: int = Field(default=4, alias="LOCAL_LLM_THREADS")
    ulm_chunk_size_chars: int = Field(default=1200, alias="ULM_CHUNK_SIZE_CHARS")
    ulm_chunk_overlap_chars: int = Field(default=200, alias="ULM_CHUNK_OVERLAP_CHARS")
    ulm_retrieval_min_score: float = Field(default=0.08, alias="ULM_RETRIEVAL_MIN_SCORE")
    ulm_url_fetch_timeout_seconds: float = Field(default=12.0, alias="ULM_URL_FETCH_TIMEOUT_SECONDS")
    ulm_url_max_content_chars: int = Field(default=40000, alias="ULM_URL_MAX_CONTENT_CHARS")
    ulm_url_user_agent: str = Field(
        default="SYNEXIS-ULM/1.0 (+local-ingestion)",
        alias="ULM_URL_USER_AGENT",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            database_url = self.database_url.strip()
            if database_url.startswith("postgres://"):
                return f"postgresql+psycopg://{database_url[len('postgres://'):]}"
            if database_url.startswith("postgresql://"):
                return f"postgresql+psycopg://{database_url[len('postgresql://'):]}"
            return database_url

        return (
            "postgresql+psycopg://"
            f"{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def auth_allowed_origins(self) -> set[str]:
        values = {
            value.strip().rstrip("/")
            for value in self.auth_allowed_origins_raw.split(",")
            if value.strip()
        }
        if not values and not self.is_production:
            values.update(
                {
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "http://localhost:4173",
                    "http://127.0.0.1:4173",
                }
            )
        return values

    def auth_trusted_device_days_for_role(self, role: str | None) -> int:
        normalized_role = (role or "user").strip().lower()
        if normalized_role == "admin":
            return max(0, self.auth_trusted_device_days_admin)
        if normalized_role == "expert":
            return max(0, self.auth_trusted_device_days_expert)
        return max(0, self.auth_trusted_device_days_user)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
