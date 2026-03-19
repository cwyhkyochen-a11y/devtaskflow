# Changelog

## v0.5.1 (2026-03-19)

**Security Fix: Shell Injection Prevention**
- `deploy_adapter.py`: Replace `shell=True` with `shlex.split()` for safe argument parsing
- `run_flow.py`: Use argument lists for npm/pip/python commands, remove `shell=True`
- Eliminates all `shell=True` usage across the codebase

## v0.5.0 (2026-03-19)

**Security Fix: ClawHub Review Response**
- `board/server.js`: Sanitize API responses — remove deploy host/user/path exposure
- `board/server.js`: Filter sensitive fields from `.state.json` (publish details, error internals)
- `landing/serve.py`: Remove hardcoded absolute path `/home/admin/.openclaw/...`, use relative paths
- `SKILL.md`: Declare optional deploy/publish env vars (`DTFLOW_GITHUB_TOKEN`, `DTFLOW_DEPLOY_SSH_KEY`, `DTFLOW_DOCKER_REGISTRY`)
- `SKILL.md`: Add board security notes (local-only, API already sanitized)

## v0.4.9 and earlier

- Initial ClawHub releases
- Core pipeline: analyze → write → review → fix → deploy → seal
- Board dashboard (Node.js + Express)
- Deploy adapters: shell, ssh_shell, docker
- Publish adapters: GitHub releases
- OpenClaw subagent orchestration
- Auto-advance mode for unattended runs
