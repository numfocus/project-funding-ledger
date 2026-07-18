[windows]
set shell := ["powershell.exe", "-NoLogo", "-Command"]

[unix]
set shell := ["sh", "-c"]

supabase-start:
    npx supabase start

dev: supabase-start
    uv run python -m flask --app project_funding_ledger run --debug
