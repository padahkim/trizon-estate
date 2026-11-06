# Codex project instructions

Read `AGENT.md` for this project's rules. The harness also includes that file in
every step prompt. Preserve the requested singular filename `AGENT.md`.

When asked to plan a harness task, follow `prompts/harness.md`. For a project
review, follow `prompts/review.md`. Read `docs/PRD.md`, `docs/ARCHITECTURE.md`,
and `docs/ADR.md` when relevant to the task.

The harness uses Codex CLI. Start an interactive project session with
`python3 scripts/codex_cli.py`; execute a prepared phase with
`python3 scripts/execute.py <phase-name>`. The launcher configures the project
command guard for that invocation. Review and trust its hook in Codex `/hooks`
before relying on it. Keep the Codex sandbox enabled.
