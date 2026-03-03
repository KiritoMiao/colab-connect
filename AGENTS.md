# AGENTS.md

## Purpose
- Guidance for coding agents working in this repository.
- Prioritize minimal, safe edits and reproducible local validation.
- Follow direct user instructions over this file if they conflict.

## Project Snapshot
- Package: `colabconnect`
- Language: Python
- Build system: `setup.py` (legacy setuptools flow)
- Main implementation: `colabconnect/colabconnect.py`
- Public API export/version: `colabconnect/__init__.py`
- Tests: none currently committed in this repo

## Repository Layout
- `colabconnect/colabconnect.py`: Colab tunnel workflow and command execution
- `colabconnect/__init__.py`: `colabconnect` export and `__version__`
- `setup.py`: package metadata and Python compatibility
- `Makefile`: `clean` and `upload` helpers
- `README.md`: usage instructions and end-user workflow

## Environment Setup
- Python requirement in metadata: `>=3.7`
- Use a virtual environment for local work
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```
- Optional dev tools:
```bash
python -m pip install black flake8 pytest twine
```

## Build, Lint, and Test Commands
### Build / Package
- Build source + wheel:
```bash
python setup.py sdist bdist_wheel
```
- Clean build outputs:
```bash
make clean
```
- Release helper (clean + build + upload):
```bash
make upload
```

### Lint / Format
- No committed lint config file was found, so default tool behavior applies.
```bash
black --check colabconnect
black colabconnect
flake8 colabconnect
```

### Test
- Current repository state: no test files are present.
- If tests are added with `pytest`:
```bash
pytest
```
- Run a single `pytest` file:
```bash
pytest tests/test_example.py
```
- Run a single `pytest` test case:
```bash
pytest tests/test_example.py::test_specific_behavior
```
- Run a single `unittest` method (if `unittest` is used):
```bash
python -m unittest tests.test_example.TestClass.test_method
```
- Quick smoke checks:
```bash
python -c "import colabconnect; print(colabconnect.__version__)"
python -m compileall colabconnect
```

## Code Style Guidelines
### Imports
- Group imports: standard library, third-party, local package.
- Prefer absolute imports unless local relative imports are clearer.
- Keep imports minimal and remove unused imports in touched files.
### Formatting
- Keep code Black-compatible and PEP 8-aligned.
- Use ~88-char wrapping style to avoid formatter churn.
- Prefer trailing commas in multiline literals/calls for cleaner diffs.
- Refactor long functions into helpers when branching gets hard to scan.
### Types and Signatures
- Add type hints for new or modified public functions.
- Preserve existing annotations and improve missing ones when practical.
- Prefer simple, concrete types; avoid unnecessary typing complexity.
### Naming Conventions
- `snake_case` for functions/variables/modules.
- `PascalCase` for classes.
- `UPPER_SNAKE_CASE` for constants.
- Use descriptive names for subprocess commands and outputs.
### Error Handling
- Validate user-facing function parameters early.
- Raise explicit exceptions with actionable messages.
- Avoid broad `except Exception` unless re-raising with context.
- Fail fast on invalid state instead of silently continuing.
### Subprocess and Shell Usage
- Prefer `subprocess.run([...], check=True)` for straightforward commands.
- Avoid `shell=True` unless command semantics require it.
- If `shell=True` is required, strictly control interpolated values.
- Surface command failures clearly; do not swallow stderr/stdout context.
### I/O and Side Effects
- Keep filesystem/network side effects explicit and easy to audit.
- Use `pathlib.Path` for path operations.
- Document behavior-changing side effects (mounts, installs, symlinks, tunnel start).
- Avoid hidden global state changes.
### Logging and User Output
- Keep progress messages short and consistent.
- Prefer structured logging in reusable library code when practical.
- Use prints sparingly for user-facing status in notebook/runtime flows.
### Dependency and Packaging Hygiene
- Keep `setup.py` metadata accurate when compatibility or behavior changes.
- Keep `colabconnect/__init__.py` version in sync with release metadata.
- Avoid adding heavy dependencies for small utility behavior.

## Repository-Specific Notes
- `colabconnect.colabconnect()` is side-effectful and environment-dependent.
- `is_colab()` checks `"google.colab" in sys.modules`; preserve unless asked.
- Default editor path is VS Code; Cursor support is opt-in via parameter.
- Runtime workflow installs helper tools in-session; changes affect onboarding.

## Cursor and Copilot Rules
- `.cursorrules`: not present
- `.cursor/rules/`: not present
- `.github/copilot-instructions.md`: not present
- If these files appear later, treat them as higher-priority local policy.

## Agent Working Agreement
- Make the smallest change that fully solves the request.
- Preserve public API behavior unless the user asks for a breaking change.
- Update docs when behavior or command usage changes.
- Add tests when introducing non-trivial behavior changes.
- Run relevant local checks before handoff.

## Suggested Pre-PR Checklist
- `black` and `flake8` pass for touched Python files.
- Package build succeeds (`python setup.py sdist bdist_wheel`).
- Import/syntax smoke checks pass.
- README examples still match behavior.
- Version values remain coherent across packaging and module exports.
