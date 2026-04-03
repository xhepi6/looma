# CLAUDE.md

- Do not include "Co-Authored-By" lines in commit messages
- Do not write unit tests or integration tests

## Running Commands

- **All commands must be run via Docker Compose** using the local compose file: `docker compose -f docker-compose.local.yml`
- **Backend commands** (pip install, alembic, python): `docker compose -f docker-compose.local.yml exec api <command>`
- **Frontend commands** (npm, npx): `docker compose -f docker-compose.local.yml exec web <command>`
- **Rebuild after dependency changes**: `docker compose -f docker-compose.local.yml up -d --build`
- **View logs**: `docker compose -f docker-compose.local.yml logs -f api` or `logs -f web`
- Do NOT run pip, python, npm, or node commands directly on the host

## Plans Directory (`docs/plans/`)

- `brainstorming_*.md` — Raw ideas that need refinement. These are rough, exploratory notes.
- `plan_*.md` — Fully detailed spec files. Each one is a refined brainstorming file turned into an actionable implementation spec with requirements, technical design, and concrete steps.

## GitHub Issues

- Use `gh issue create`. Always include a type label, a `priority:` label, a `complexity:` label, and relevant domain labels.
- **Type**: `bug`, `enhancement`, `cleanup`, `documentation`
- **Priority**: `priority: critical`, `priority: high`, `priority: medium`, `priority: low`
- **Complexity**: `complexity: small` (hours), `complexity: medium` (days), `complexity: large` (week+), `complexity: epic` (multi-week)
- **Domain**: `voice`, `dashboard`, `tooling`, `infrastructure`, `performance`, `monitoring`
- Title: short, imperative ("Fix ...", "Add ...", "Expand ..."). Body: `## Summary/Bug/Problem` → details → `## Impact/Goal`.
- Use `**bold**` for key terms, `###` subsections for long bodies, reference file paths when relevant.
- Pass body via heredoc: `--body "$(cat <<'EOF' ... EOF)"`
- Check existing issues (`gh issue list`) for style reference.

## Solving GitHub Issues

When asked to solve an issue (e.g. "lets solve issue #13"):

1. **Pull & read the issue**: `git pull`, then `gh issue view <number>` to get full context
2. **Explore the code**: Investigate the relevant files and understand the root cause before writing any code
3. **Create a branch**: `git checkout -b fix/<short-description>` (or `feat/` for enhancements, `cleanup/` for cleanup)
4. **Implement the fix**: Make the minimal, focused change that addresses the issue
5. **Verify**: Syntax check, grep to confirm changes are correct, and manual testing where applicable
6. **Commit**: Short message explaining the "why", include `Closes #<number>` in the body
7. **Push & PR**: Push the branch, create a PR with `gh pr create`. PR body should be short and high-level: what was fixed, and bullet points on how to test as a user
8. **Keep it tight**: No over-engineering, no unrelated changes, no tests (per project rules)
