# Project Mandates

- **Tooling:** Strictly use `uv` for package management and commands. **Do not use `pip`.**
- **Code Quality:** Maintain strict domain models (do not arbitrarily widen type unions to appease checkers). All functions require complete type hints.
- **Validation:** Before completing any task, you MUST run and fix all errors for: `uv run ruff check . --fix && uv run ruff format . && uv run pyrefly check . && uv run pytest`.
- **Error Handling:** Fail fast. Propagate exceptions for logging. Do NOT use broad `except Exception:` blocks or fallback values to silently hide failures.
- **Source Control:** NEVER commit, run `git merge`, or mutate git history. The user handles all git operations manually.
