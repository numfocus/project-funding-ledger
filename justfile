[windows]
set shell := ["powershell.exe", "-NoLogo", "-Command"]

[unix]
set shell := ["sh", "-c"]

dev:
    uv run python -m flask --app project_funding_ledger run --debug
