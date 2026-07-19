-- Migration to create organization_import_batch and organization_import_row tables.
-- organization_import_batch tracks the Excel upload session.
-- organization_import_row tracks individual proposed creates and updates for review.

-- 1. Create organization_import_batch table
create table public.organization_import_batch (
    id uuid primary key default gen_random_uuid(),
    file_name text not null,
    created_by_user_id uuid references public.user_profile(id) on delete set null,
    created_at timestamp with time zone not null default now()
);

-- Indexing for organization_import_batch
create index idx_org_import_batch_created_at on public.organization_import_batch(created_at desc);

-- Enable RLS for organization_import_batch
alter table public.organization_import_batch enable row level security;
grant select, insert, update, delete on table public.organization_import_batch to authenticated, service_role;

-- RLS Policies for organization_import_batch (Only Admins have access)
create policy "Admin access only for batch"
on public.organization_import_batch for all
to authenticated
using (public.is_system_admin())
with check (public.is_system_admin());


-- 2. Create organization_import_row table
create table public.organization_import_row (
    id uuid primary key default gen_random_uuid(),
    batch_id uuid not null references public.organization_import_batch(id) on delete cascade,
    import_key text not null,
    action_type text not null check (action_type in ('Create', 'Update')),
    status text not null default 'Pending' check (status in ('Pending', 'Confirmed', 'Cancelled', 'Error')),
    organization_data jsonb not null default '{}'::jsonb,
    diff_data jsonb,
    error_message text,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    resolved_by_user_id uuid references public.user_profile(id) on delete set null,
    resolved_at timestamp with time zone
);

-- Indexing for organization_import_row
create index idx_org_import_row_batch_id on public.organization_import_row(batch_id);
create index idx_org_import_row_status on public.organization_import_row(status);
create index idx_org_import_row_import_key on public.organization_import_row(import_key);

-- Trigger for organization_import_row updated_at
create trigger update_organization_import_row_updated_at
    before update on public.organization_import_row
    for each row
    execute function public.update_updated_at_column();

-- Enable RLS for organization_import_row
alter table public.organization_import_row enable row level security;
grant select, insert, update, delete on table public.organization_import_row to authenticated, service_role;

-- RLS Policies for organization_import_row (Only Admins have access)
create policy "Admin access only for row"
on public.organization_import_row for all
to authenticated
using (public.is_system_admin())
with check (public.is_system_admin());
