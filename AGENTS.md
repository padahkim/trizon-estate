# Codex project instructions

Read `AGENT.md` for this project's rules. The harness also includes that file in
every step prompt. Preserve the requested singular filename `AGENT.md`.

Use this repository's harness workflow. Do not invoke `superpowers:*` skills,
create `docs/superpowers/` specs or plans, or substitute a skill's planning,
review, worktree, delegation, or commit workflow for the project harness.
The user explicitly opted out of superpowers for this repository.

The canonical product documents are `docs/PRD.md`, `docs/ARCHITECTURE.md`, and
`docs/ADR.md`. Keep agreed requirements and technical decisions there: the
harness injects only `AGENT.md` and top-level `docs/*.md` into each step.
`docs/archive/` is historical context and is not an active implementation spec.
Distinguish confirmed user requirements from proposals. Discuss material stack
or scope changes with the user before treating them as settled.

When asked to plan a harness task, follow `prompts/harness.md`. For a project
review, follow `prompts/review.md`. Read `docs/PRD.md`, `docs/ARCHITECTURE.md`,
and `docs/ADR.md` when relevant to the task.

The harness uses Codex CLI. Start an interactive project session with
`python3 scripts/codex_cli.py`; execute a prepared phase with
`python3 scripts/execute.py <phase-name>`. The launcher configures the project
command guard for that invocation. Review and trust its hook in Codex `/hooks`
before relying on it. Keep the Codex sandbox enabled.
