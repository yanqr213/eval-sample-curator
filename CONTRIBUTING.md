# Contributing

Thanks for helping improve `eval-sample-curator`.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

## Development guidelines

- Keep the default path offline and dependency-light.
- Prefer standard library code unless a dependency clearly improves reliability.
- Add focused tests for loader behavior, selection reasons, output shape, and CLI exit codes.
- Do not include real prompts, user data, credentials, or production eval traces in tests.
- For redaction changes, include examples that cover both true positives and likely false positives.

## Pull request checklist

- Tests pass with `python -m pytest`.
- Public behavior is documented in `README.md` or `CHANGELOG.md`.
- New examples are synthetic or fully anonymized.
