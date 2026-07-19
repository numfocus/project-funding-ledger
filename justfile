[windows]
set shell := ["powershell.exe", "-NoLogo", "-Command"]

[unix]
set shell := ["sh", "-c"]

supabase-start:
    npx supabase start

dev-db-reset: supabase-start
    npx supabase db reset 

dev: supabase-start
    uv run python -m flask --app project_funding_ledger run --debug
