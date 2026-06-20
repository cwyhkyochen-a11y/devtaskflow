---
name: devtaskflow
description: Use DevTaskFlow when a user wants to start, continue, govern, or release a tracked software project from plain-language requirements. Trigger for new app/tool/platform ideas, adding project memory and governance to an existing repo while continuing development, resuming a DevTaskFlow project, checking what stage a project is in, identifying missing requirements or blockers, running AI-assisted analysis/implementation/review/fix/preview/deploy flows, sealing a version, or publishing a generated project. Do not force DevTaskFlow for isolated one-off edits unless the user asks for project tracking, long-running goal work, governance, versioning, or release discipline.
---

# DevTaskFlow

DevTaskFlow is a Codex skill plus CLI for running a software-development pipeline from natural language: requirements -> plan -> code -> review -> fixes -> final review -> local preview -> deploy -> release.

It also carries a light personal-project standard layer for durable project memory: `AGENTS.md`, `docs/project/`, `docs/process/`, `docs/decisions/`, `docs/versions/`, and `ops/` when deployment is in scope.

## Before Acting

- Use DevTaskFlow directly when the user explicitly asks for `$devtaskflow`, a tracked goal project, versioned development, governance, progress tracking, preview/deploy/release flow, or continuing an existing DevTaskFlow project.
- Suggest DevTaskFlow, then ask before creating files, when the request only implicitly looks like a long-running project or existing-repo governance task.
- Do not force DevTaskFlow for small one-off bug fixes, code reviews, refactors, or explanations unless the user asks to bring that work under project tracking.
- If the user's request is vague, first clarify only the missing decision that blocks the next stage, such as audience, core workflow, login/auth needs, data model, integrations, deployment target, or acceptance criteria.
- Run commands from the project root that contains `.dtflow/config.json`. For a new tracked project or an existing repo being brought under DevTaskFlow, `dtflow start --new-project` creates the structure.
- If Python dependencies are missing, install them with `pip install -r requirements.txt` from the DevTaskFlow skill directory.
- For personal long-running projects, multi-window work, subagent work, handoff memory, or version freeze, read `references/personal-project-standards.md` before deciding the project structure or release steps.
- Treat analyze, review, final review, and seal as standards-driven gates: do not skip missing non-goals, acceptance criteria, version docs, tests, deployment notes, or release-freeze blockers.
- Before `seal`, deploy, publish, commit, tag, or any command that produces release/git side effects, ask for explicit user authorization.

## Codex Runtime

DevTaskFlow for Codex does not use a separate model endpoint, API key, hidden Codex session, or external orchestrator.

Codex handles reasoning, implementation, edits, review, and tool execution in the current session. DevTaskFlow only provides project structure, durable state, stage guidance, checklists, board/status commands, local preview helpers, deployment helpers, and release discipline.

Never ask the user to configure model credentials, model names, external model endpoints, or local keychains for the Codex skill workflow. Never read Codex account files, session files, hidden credentials, or local keychains.

## Core Commands

```bash
dtflow setup
dtflow start --new-project --name NAME --idea "需求"
dtflow start
dtflow start --confirm
dtflow start --confirm-write
dtflow start --feedback "修改意见"
dtflow start --run
dtflow start --final-review
dtflow start --deploy
dtflow board
dtflow board --serve
dtflow board-query --name PROJECT
dtflow advanced publish --target github
```

## Entry Modes

### New Tracked Project

Use this when the user wants to build a new app, tool, internal system, dashboard, automation, SDK, script, or platform as a tracked goal.

1. Run `dtflow start --new-project --name NAME --idea "user's original requirement"`.
2. Confirm the project skeleton includes `AGENTS.md`, stable project docs, process docs, decisions, and `docs/versions/`.
3. Show the generated requirement suggestions and ask whether the user wants to add anything.
4. Continue with `dtflow start --confirm` after the user approves the plan.
5. Use `dtflow start --confirm-write` after previewing the write plan.
6. Let the current Codex session implement, review, and fix tasks while DevTaskFlow records status and handoff notes.
7. Run `dtflow start --final-review` before deployment unless the user explicitly asks to skip it.
8. Run `dtflow start --run` for local preview and give the local URL to the user.
9. Deploy only after the user confirms the preview.

### Existing Repo Governance And Development

Use this when the user has an existing project and wants DevTaskFlow to add structure, memory, version discipline, or goal-driven development while continuing real implementation work.

1. Inspect the repo first: read `AGENTS.md` if present, existing README/docs, package files, test/build commands, and current git status.
2. If `.dtflow/config.json` is missing, ask before adding DevTaskFlow files, then run `dtflow start --new-project --path /absolute/repo/path --name NAME --idea "governance and development goal"`.
3. Keep existing project conventions as the source of truth; DevTaskFlow docs should record and organize them, not replace them.
4. Fill or flag gaps in `docs/project/`, `docs/process/`, `docs/versions/`, and `AGENTS.md`: purpose, target users, core workflow, non-goals, acceptance criteria, commands, risks, deployment notes, and rollback method.
5. Continue with the same staged workflow as a new project: Codex analyzes, implements, reviews, and fixes; DevTaskFlow records status, handoff notes, preview/deploy helpers, and seal checks.

### Existing DevTaskFlow Project

Use this when `.dtflow/config.json` already exists or the user asks to continue/check progress.

- To continue the current project, run `dtflow start`.
- To add a small change request, run `dtflow start --feedback "user feedback"`.
- For major scope changes, do not overwrite the current version. Ask whether to finish/seal the current version first, use the already-created next version after sealing, or start a separate tracked project.
- To inspect progress, use `dtflow board` or `dtflow board-query --name PROJECT`.
- For sealed versions, treat new scope as the next version unless the user explicitly asks for a patch or erratum.

## Stage Orientation

When entering an existing DevTaskFlow project, orient before acting:

1. Find the project root with `.dtflow/config.json`.
2. Run `dtflow advanced status` from the project root, or `dtflow board-query --name PROJECT` from the workspace.
3. Read `AGENTS.md`, current `docs/project/` files, current `docs/versions/<version>/docs/REQUIREMENTS.md`, and current review/final-review docs when present.
4. Check `.state.json` only as internal state. Use it to identify `status`, `current_task`, `tasks`, `last_summary`, and `last_error`, but do not expose raw state files to the user.
5. Report the current stage, the next useful action, and any missing blockers in plain language.

## Stage Actions

| State | Meaning | Default action |
| --- | --- | --- |
| `initialized` / `created` | Project or version exists, requirements may be incomplete | Collect or add the version goal, target users, core workflow, scope, non-goals, and acceptance criteria; then run `dtflow start`. |
| `pending_confirm` | Analysis plan is ready | Summarize plan and gaps; run `dtflow start --confirm` only after approval, or `dtflow start --feedback "..."` for changes. |
| `confirmed` | Plan is approved | Run `dtflow start` to preview the write plan. |
| `writing` / `written` | Code generation is underway or just completed | Let review continue with `dtflow start`; summarize files and next review stage. |
| `reviewing` | Task review is underway | Wait or continue with `dtflow start`; do not deploy yet. |
| `needs_fix` / `fixing` | Review found issues | Run `dtflow start` to fix and re-review; surface blocker themes without dumping raw review files. |
| `review_passed` | A task or all tasks passed review | Run `dtflow start` to move to the next task; if no tasks remain, prepare final review. |
| `pending_final_review` | All task reviews passed; final review is next | Recommend context compaction if needed, then run `dtflow start --final-review`. |
| `ready_to_deploy` | Final review passed | Offer local preview with `dtflow start --run`; deploy only after user confirmation. |
| `needs_final_fix` | Final review found blockers | Run `dtflow start` to fix final-review issues; report missing tests, docs, deployment notes, or acceptance gaps. |
| `deployed` / `all_done` | Deployment or all work is complete | Offer seal/release-freeze; run seal only after explicit authorization. |
| `sealed` | Version is finalized | Treat new scope as a new version, patch, or erratum based on user intent. |
| `failed` | Last action failed | Run `dtflow advanced status` and, if needed, `dtflow advanced doctor` or `dtflow advanced recover`; explain `last_error` plainly. |

## Missing Context To Surface

Always surface missing context when it affects the next stage:

- Product: version goal, target users, core workflow, functional scope, non-goals, data scope, acceptance criteria.
- Engineering: stack, existing conventions, typecheck/test/build commands, important error paths, migration needs.
- Design: target device sizes, density, key screens, empty/error states, copy quality, usability risks.
- Operations: deployment target, build artifact, deploy method, preview URL, verification, rollback method.
- Release: unresolved P0/P1 tasks, placeholders, failed checks, dirty git status, missing changelog, unapproved commit/tag/publish steps.

## Personal Project Standard

- Keep stable project facts in `docs/project/`; keep version facts in `docs/versions/`; keep cross-version decisions in `docs/decisions/`.
- Treat `AGENTS.md` as the project-level collaboration contract and reading map. Do not put private machine paths, secrets, temporary prompts, or one-person-only preferences there.
- During analysis, require a version goal, target users, core workflow, functional scope, explicit non-goals, data scope, acceptance criteria, risks, and dependencies.
- During review, include product copy quality, design usability, development tests, observable error paths, and deployment readiness when relevant.
- When the user says "封版", run the release-freeze checks before commit, tag, deployment archive, or release publishing; blockers must be fixed or explicitly moved into an accepted patch/erratum flow.

## Status Language

Translate internal states into user-facing language:

| State | Meaning | User-facing summary |
| --- | --- | --- |
| `initialized` / `created` | Project/version created | "项目已创建，正在补齐目标和需求。" |
| `pending_confirm` | Plan ready | "方案已生成，等你确认或补充。" |
| `confirmed` | Approved | "已确认，开始生成代码。" |
| `writing` / `written` | Code generation underway/done | "代码已生成，我在审查。" |
| `needs_fix` | Review found issues | "发现问题，正在修复并复审。" |
| `review_passed` | Task review passed | "任务级审查通过，可以做最终审查。" |
| `ready_to_deploy` | Final review passed | "最终审查通过，可以预览或部署。" |
| `needs_final_fix` | Final review failed | "最终审查发现问题，需要修复。" |
| `failed` | Last action failed | "上一步失败，我会先定位原因和可恢复路径。" |
| `sealed` | Version finalized | "版本已封版。" |

## What To Show

- Show concise progress, decisions, preview URLs, review summaries, and next steps.
- Avoid exposing implementation internals such as `DEV_PLAN.md`, `.state.json`, raw orchestration payloads, hidden config files, API keys, or token counts.
- For failures, summarize the likely cause and next command to try. Use `dtflow advanced doctor` for environment diagnostics.

## Notes

- `dtflow setup` is interactive; in non-interactive Codex work, prefer writing `.env` only when the user has explicitly provided credentials.
- The board server is local-only and defaults to port `8765`.
- `dtflow start --deploy` currently deploys and then seals through auto-advance. Treat it as a release action that needs explicit authorization, not as a lightweight preview.
- Docker deployment requires Docker. GitHub release publishing requires `gh` to be installed and authenticated.
- The default orchestration is `codex_managed`: current Codex session does the intelligent work; `dtflow` records state and writes `CODEX_NEXT_ACTION.md` handoff notes when needed.
