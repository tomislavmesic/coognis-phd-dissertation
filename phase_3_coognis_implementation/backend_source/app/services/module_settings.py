from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AppSetting
from app.services.local_llm import get_supported_llm_options, normalize_llm_selection


@dataclass
class ModuleSettingsState:
    synapse_enabled: bool
    uex_enabled: bool
    ulm_enabled: bool
    page_enabled: bool
    llm_provider: str
    llm_model: str


@dataclass
class GeneralSettingsState:
    show_chat_debug_panels: bool
    verbose_routing_logs: bool
    allow_expert_handoff: bool
    allow_ulm_in_chat: bool


class ModuleSettingsService:
    SETTING_KEYS = {
        "synapse_enabled": "mind.enable_synapse",
        "uex_enabled": "mind.enable_uex",
        "ulm_enabled": "mind.enable_ulm",
        "page_enabled": "mind.enable_page",
        "llm_provider": "llm.provider",
        "llm_model": "llm.model",
    }
    GENERAL_SETTING_KEYS = {
        "show_chat_debug_panels": "mind.show_chat_debug_panels",
        "verbose_routing_logs": "mind.verbose_routing_logs",
        "allow_expert_handoff": "mind.allow_expert_handoff",
        "allow_ulm_in_chat": "mind.allow_ulm_in_chat",
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_settings(self) -> ModuleSettingsState:
        defaults = self._default_state()
        rows = self.db.execute(
            select(AppSetting).where(AppSetting.key.in_(self.SETTING_KEYS.values()))
        ).scalars().all()
        values = {row.key: row.value for row in rows}
        selection = normalize_llm_selection(
            values.get(self.SETTING_KEYS["llm_provider"], defaults.llm_provider),
            values.get(self.SETTING_KEYS["llm_model"], defaults.llm_model),
        )

        return ModuleSettingsState(
            synapse_enabled=self._parse_bool(values.get(self.SETTING_KEYS["synapse_enabled"]), defaults.synapse_enabled),
            uex_enabled=self._parse_bool(values.get(self.SETTING_KEYS["uex_enabled"]), defaults.uex_enabled),
            ulm_enabled=self._parse_bool(values.get(self.SETTING_KEYS["ulm_enabled"]), defaults.ulm_enabled),
            page_enabled=self._parse_bool(values.get(self.SETTING_KEYS["page_enabled"]), defaults.page_enabled),
            llm_provider=selection.provider,
            llm_model=selection.model,
        )

    def update_settings(
        self,
        *,
        synapse_enabled: bool | None = None,
        uex_enabled: bool | None = None,
        ulm_enabled: bool | None = None,
        page_enabled: bool | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
    ) -> ModuleSettingsState:
        updates = {
            "synapse_enabled": synapse_enabled,
            "uex_enabled": uex_enabled,
            "ulm_enabled": ulm_enabled,
            "page_enabled": page_enabled,
        }

        for field, value in updates.items():
            if value is None:
                continue
            key = self.SETTING_KEYS[field]
            row = self.db.get(AppSetting, key)
            if row is None:
                row = AppSetting(key=key, value=self._format_bool(value))
                self.db.add(row)
            else:
                row.value = self._format_bool(value)

        if llm_provider is not None or llm_model is not None:
            current = self.get_settings()
            selection = normalize_llm_selection(
                llm_provider or current.llm_provider,
                llm_model or current.llm_model,
            )
            self._set_string_setting("llm_provider", selection.provider)
            self._set_string_setting("llm_model", selection.model)

        self.db.commit()
        return self.get_settings()

    def get_general_settings(self) -> GeneralSettingsState:
        defaults = self._default_general_state()
        rows = self.db.execute(
            select(AppSetting).where(AppSetting.key.in_(self.GENERAL_SETTING_KEYS.values()))
        ).scalars().all()
        values = {row.key: row.value for row in rows}

        return GeneralSettingsState(
            show_chat_debug_panels=self._parse_bool(
                values.get(self.GENERAL_SETTING_KEYS["show_chat_debug_panels"]),
                defaults.show_chat_debug_panels,
            ),
            verbose_routing_logs=self._parse_bool(
                values.get(self.GENERAL_SETTING_KEYS["verbose_routing_logs"]),
                defaults.verbose_routing_logs,
            ),
            allow_expert_handoff=self._parse_bool(
                values.get(self.GENERAL_SETTING_KEYS["allow_expert_handoff"]),
                defaults.allow_expert_handoff,
            ),
            allow_ulm_in_chat=self._parse_bool(
                values.get(self.GENERAL_SETTING_KEYS["allow_ulm_in_chat"]),
                defaults.allow_ulm_in_chat,
            ),
        )

    def update_general_settings(
        self,
        *,
        show_chat_debug_panels: bool | None = None,
        verbose_routing_logs: bool | None = None,
        allow_expert_handoff: bool | None = None,
        allow_ulm_in_chat: bool | None = None,
    ) -> GeneralSettingsState:
        updates = {
            "show_chat_debug_panels": show_chat_debug_panels,
            "verbose_routing_logs": verbose_routing_logs,
            "allow_expert_handoff": allow_expert_handoff,
            "allow_ulm_in_chat": allow_ulm_in_chat,
        }

        for field, value in updates.items():
            if value is None:
                continue
            key = self.GENERAL_SETTING_KEYS[field]
            row = self.db.get(AppSetting, key)
            if row is None:
                row = AppSetting(key=key, value=self._format_bool(value))
                self.db.add(row)
            else:
                row.value = self._format_bool(value)

        self.db.commit()
        return self.get_general_settings()

    def get_llm_options(self):
        return get_supported_llm_options()

    @staticmethod
    def _parse_bool(value: str | None, default: bool) -> bool:
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _format_bool(value: bool) -> str:
        return "true" if value else "false"

    def _set_string_setting(self, field: str, value: str) -> None:
        key = self.SETTING_KEYS[field]
        row = self.db.get(AppSetting, key)
        if row is None:
            row = AppSetting(key=key, value=value)
            self.db.add(row)
        else:
            row.value = value

    @staticmethod
    def _default_state() -> ModuleSettingsState:
        selection = normalize_llm_selection(settings.llm_provider, settings.llm_model)
        return ModuleSettingsState(
            synapse_enabled=settings.mind_enable_synapse,
            uex_enabled=settings.mind_enable_uex,
            ulm_enabled=settings.mind_enable_ulm,
            page_enabled=settings.mind_enable_page,
            llm_provider=selection.provider,
            llm_model=selection.model,
        )

    @staticmethod
    def _default_general_state() -> GeneralSettingsState:
        return GeneralSettingsState(
            show_chat_debug_panels=False,
            verbose_routing_logs=True,
            allow_expert_handoff=True,
            allow_ulm_in_chat=True,
        )
