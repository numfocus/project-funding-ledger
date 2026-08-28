[windows]
set shell := ["powershell.exe", "-NoLogo", "-Command"]

[unix]
set shell := ["sh", "-c"]

supabase-start:
    npx supabase start

dev-db-reset: supabase-start
    npx supabase db reset 

dev-db-dump: supabase-start
    npx supabase db dump --data-only --local -f ./supabase/seed.sql

redis-start:
    {{ if os() == "windows" { "if (docker ps -a --filter name=local-redis -q) { docker start local-redis } else { docker run -d --name local-redis -p 6379:6379 redis:alpine }" } else { "docker start local-redis 2>/dev/null || docker run -d --name local-redis -p 6379:6379 redis:alpine" } }}

celery-worker: redis-start
    {{ if os() == "windows" { "uv run celery -A project_funding_ledger.queue.celery_worker:celery_app worker --loglevel=info -P solo" } else { "uv run celery -A project_funding_ledger.queue.celery_worker:celery_app worker --loglevel=info" } }}

celery-start: redis-start
    {{ if os() == "windows" { "Start-Process uv -ArgumentList 'run', 'celery', '-A', 'project_funding_ledger.queue.celery_worker:celery_app', 'worker', '--loglevel=info', '-P', 'solo'" } else { "uv run celery -A project_funding_ledger.queue.celery_worker:celery_app worker --loglevel=info &" } }}

dev: supabase-start celery-start
    uv run python -m flask --app project_funding_ledger run --debug

