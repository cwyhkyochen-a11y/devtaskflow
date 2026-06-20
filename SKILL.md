---
name: devtaskflow
description: Use DevTaskFlow when a user wants to turn a plain-language software idea into a tracked, runnable project with AI-assisted analysis, implementation, review, fixing, preview, deployment, or GitHub release publishing. Trigger for requests like building an app/tool/platform from a requirement, continuing a DevTaskFlow project, checking project progress, running the local preview board, performing final review, deploying, or publishing a generated project.
---

# DevTaskFlow

DevTaskFlow is a Codex skill plus CLI for running a full software-development pipeline from natural language: requirements -> plan -> code -> review -> fixes -> final review -> local preview -> deploy -> release.

## Before Acting

- Suggest DevTaskFlow when the user describes a software product, tool, internal system, dashboard, workflow automation, or app they want built.
- Ask for confirmation before starting a new DevTaskFlow project because the workflow can create files, run tools, call an LLM, and consume substantial tokens.
- If the user's request is vague, first clarify audience, core workflow, login/auth needs, data model, integrations, and preferred deployment target.
- Run commands from the project root that contains `.dtflow/config.json`. For a new project, `dtflow start --new-project` creates the structure.
- If Python dependencies are missing, install them with `pip install -r requirements.txt` from the DevTaskFlow skill directory.

## LLM Configuration

DevTaskFlow calls an OpenAI-compatible `/chat/completions` endpoint. Configure one of these before running generation:

```bash
DTFLOW_LLM_BASE_URL=https://api.openai.com/v1
DTFLOW_LLM_API_KEY=sk-...
DTFLOW_LLM_MODEL=<model-id-available-to-the-user>
```

Codex-friendly fallbacks are also supported:

- `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`
- Project `.env`
- Optional independent orchestration variables: `DTFLOW_CODEX_BASE_URL`, `DTFLOW_CODEX_API_KEY`, `DTFLOW_CODEX_MODEL`

Do not read or expose Codex account/session files. Ask the user to provide an explicit API key or environment variable when configuration is missing.

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

## New Project Workflow

1. Run `dtflow start --new-project --name NAME --idea "user's original requirement"`.
2. Show the generated requirement suggestions and ask whether the user wants to add anything.
3. Continue with `dtflow start --confirm` after the user approves the plan.
4. Use `dtflow start --confirm-write` after previewing the write plan.
5. Let DevTaskFlow run review/fix loops until task review passes.
6. Run `dtflow start --final-review` before deployment unless the user explicitly asks to skip it.
7. Run `dtflow start --run` for local preview and give the local URL to the user.
8. Deploy only after the user confirms the preview.

## Existing Project Workflow

- To continue the current project, run `dtflow start`.
- To add a small change request, run `dtflow start --feedback "user feedback"`.
- For major scope changes, suggest starting a new version with `dtflow advanced version --new` rather than rewriting the current version.
- To inspect progress, use `dtflow board` or `dtflow board-query --name PROJECT`.

## Status Language

Translate internal states into user-facing language:

| State | Meaning | User-facing summary |
| --- | --- | --- |
| `created` | Project/version created | "项目已创建，正在分析需求。" |
| `pending_confirm` | Plan ready | "方案已生成，等你确认或补充。" |
| `confirmed` | Approved | "已确认，开始生成代码。" |
| `writing` / `written` | Code generation underway/done | "代码已生成，我在审查。" |
| `needs_fix` | Review found issues | "发现问题，正在修复并复审。" |
| `review_passed` | Task review passed | "任务级审查通过，可以做最终审查。" |
| `ready_to_deploy` | Final review passed | "最终审查通过，可以预览或部署。" |
| `needs_final_fix` | Final review failed | "最终审查发现问题，需要修复。" |
| `sealed` | Version finalized | "版本已封版。" |

## What To Show

- Show concise progress, decisions, preview URLs, review summaries, and next steps.
- Avoid exposing implementation internals such as `DEV_PLAN.md`, `.state.json`, raw orchestration payloads, hidden config files, API keys, or token counts.
- For failures, summarize the likely cause and next command to try. Use `dtflow advanced doctor` for environment diagnostics.

## Notes

- `dtflow setup` is interactive; in non-interactive Codex work, prefer writing `.env` only when the user has explicitly provided credentials.
- The board server is local-only and defaults to port `8765`.
- Docker deployment requires Docker. GitHub release publishing requires `gh` to be installed and authenticated.
- `codex_subagent` is an optional OpenAI-compatible orchestration mode configured through the `codex` block; `local_llm` remains the default.
