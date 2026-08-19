---
name: authenticated-browser-ops
description: Execute authorized research and submission workflows in a real browser while reusing a user-established login session. Use for paywalled-library access the user is entitled to, database searches, lawful PDF downloads, venue portals, form filling, file uploads, or site-specific tasks that require persistent cookies, SSO, extensions, or an existing browser profile.
---

# Authenticated Browser Operations

1. Select the configured provider. Prefer `ego-browser` with ego (lite) Spaces on macOS; on Windows use the approved Chrome/session-profile fallback. Never silently move cookies between providers.
2. Verify the requested domain against the allowlist and bind the task to the least-privileged named profile/Space.
3. Assume the human established the login. Never ask for or place passwords, session cookies, one-time codes, or recovery secrets in prompts, commands, logs, or artifacts.
4. Open a new isolated task Space/session, read a snapshot, and verify the account and target site before acting.
5. Compose a bounded workflow: navigate → observe → act → wait → extract/download/upload → verify. Prefer one deterministic script for stable repeated operations.
6. Store only metadata needed for reproducibility: URL, retrieval time, query, downloaded file hash, entitlement/source, and final status. Do not persist raw auth state in the project.
7. Respect robots rules, database licenses, publisher terms, download limits, copyright, and institutional access. Do not bypass paywalls or access controls.
8. Pause for CAPTCHA, 2FA, changed terms, payment, identity verification, unexpected permission prompts, or an unapproved external side effect.
9. For submission portals, prepare fields and uploads, run a visual/semantic verification, then execute final submission only when the workflow contains a fresh human approval bound to the artifact hashes.
10. Capture the receipt/confirmation and verify the resulting server-side status. Never infer success from a click alone.
11. Close/complete the task Space without deleting the durable user profile. Revoke the task lease after completion.

Return:

```json
{
  "provider": "ego-browser|chrome-control|agent-browser-profile",
  "profile_alias": "non-secret alias",
  "domains": [],
  "actions": [],
  "downloads": [{"path": "...", "sha256": "...", "source_url": "..."}],
  "external_effect": "none|draft|submitted",
  "verification": "verified|needs-human|failed",
  "receipt": null
}
```

Do not claim that `ego-browser` ran when the host is not macOS or ego (lite) is not installed and connected.

