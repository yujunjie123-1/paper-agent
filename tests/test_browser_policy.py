from pathlib import Path

import pytest

from paper_agents.browser_policy import BrowserPolicy, BrowserProvider


def write_config(path: Path, allowed_domains: list[str]) -> Path:
    domains = ", ".join(allowed_domains)
    path.write_text(
        f"""
default_by_platform:
  darwin: ego-lite
  windows: chrome-control
  linux: agent-browser-profile
profiles:
  scholarly-search:
    allowed_domains: [{domains}]
""",
        encoding="utf-8",
    )
    return path


def test_windows_uses_authenticated_chrome_fallback(tmp_path: Path, monkeypatch) -> None:
    policy = BrowserPolicy(write_config(tmp_path / "browser.yaml", ["example.org"]))
    monkeypatch.setattr("paper_agents.browser_policy.platform.system", lambda: "Windows")

    lease = policy.lease(
        profile_alias="scholarly-search",
        urls=["https://example.org/search?q=agents"],
    )

    assert lease.provider == BrowserProvider.CHROME_CONTROL
    assert lease.domains == ("example.org",)
    assert lease.approval_gate is None


def test_browser_policy_denies_unlisted_domain(tmp_path: Path) -> None:
    policy = BrowserPolicy(write_config(tmp_path / "browser.yaml", ["example.org"]))

    with pytest.raises(PermissionError, match="outside allowlist"):
        policy.lease(
            profile_alias="scholarly-search",
            urls=["https://malicious.example/search"],
        )


def test_external_browser_write_requires_submission_gate(tmp_path: Path) -> None:
    policy = BrowserPolicy(write_config(tmp_path / "browser.yaml", ["example.org"]))

    lease = policy.lease(
        profile_alias="scholarly-search",
        urls=["https://example.org/submit"],
        external_write=True,
    )

    assert lease.approval_gate == "submission"
