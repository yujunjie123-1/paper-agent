from __future__ import annotations

import platform
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse

import yaml

from .config import PROJECT_ROOT


class BrowserProvider(StrEnum):
    EGO_LITE = "ego-lite"
    CHROME_CONTROL = "chrome-control"
    AGENT_BROWSER_PROFILE = "agent-browser-profile"


@dataclass(frozen=True)
class BrowserTaskLease:
    provider: BrowserProvider
    profile_alias: str
    domains: tuple[str, ...]
    approval_gate: str | None = None


class BrowserPolicy:
    """Selects a provider and enforces domain/profile boundaries; it stores no secrets."""

    def __init__(self, path: Path | None = None) -> None:
        config_path = path or PROJECT_ROOT / "config" / "browser_providers.yaml"
        self.config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    def platform_default(self) -> BrowserProvider:
        system = platform.system().lower()
        key = "darwin" if system == "darwin" else "windows" if system == "windows" else "linux"
        return BrowserProvider(self.config["default_by_platform"][key])

    def lease(
        self,
        *,
        profile_alias: str,
        urls: list[str],
        external_write: bool = False,
    ) -> BrowserTaskLease:
        profile = self.config["profiles"].get(profile_alias)
        if profile is None:
            raise ValueError(f"Unknown browser profile alias: {profile_alias}")
        domains = tuple(sorted({urlparse(url).hostname or "" for url in urls}))
        allowed = set(profile["allowed_domains"])
        if not allowed:
            raise PermissionError(f"Profile {profile_alias} has no configured domain allowlist")
        if not set(domains) <= allowed:
            raise PermissionError(f"Browser task requests domains outside allowlist: {domains}")
        return BrowserTaskLease(
            provider=self.platform_default(),
            profile_alias=profile_alias,
            domains=domains,
            approval_gate="submission" if external_write else None,
        )

