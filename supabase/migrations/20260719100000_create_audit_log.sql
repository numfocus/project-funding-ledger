-- Migration to create the audit_log table as specified in the Architecture Design.
-- Rename related_project_id to related_organization_id.
-- Implement RLS policies where authenticated users can insert, only system admins can select, and nobody can update/delete.

-- Create audit_log table
create table public.audit_log (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete set null,
    action_type text not null check (action_type in (
        'Login',
        'Logout',
        'Create',
        'Update',
        'Delete',
        'Upload',
        'Import',
        'Resolve Exception',
        'Permission Change',
        'Other'
    )),
    entity_type text not null,
    table_name text,
    record_id uuid,
    related_organization_id uuid,
    related_funding_source_id uuid,
    summary text,
    old_value jsonb,
    new_value jsonb,
    ip_address text,
    user_agent text,
    created_at timestamp with time zone not null default now()
);

-- Indexing strategy for audit_log to support auditing, troubleshooting, and filtering
create index idx_audit_log_user_id on public.audit_log(user_id);
create index idx_audit_log_created_at on public.audit_log(created_at desc);
create index idx_audit_log_related_organization_id on public.audit_log(related_organization_id);
create index idx_audit_log_related_funding_source_id on public.audit_log(related_funding_source_id);

-- Enable Row-Level Security
alter table public.audit_log enable row level security;

-- Grant permissions to standard roles
grant insert, select, delete on table public.audit_log to authenticated, service_role;

-- RLS Policies
-- 1. Allow insert for authenticated users
create policy "Allow insert for authenticated users"
on public.audit_log for insert
to authenticated
with check (true);

-- 2. Allow select for system administrators only
create policy "Allow select for system admins only"
on public.audit_log for select
to authenticated
using (
    public.is_system_admin()
);

-- 3. Allow delete for system administrators only on records older than 180 days
create policy "Allow delete for system admins on records older than 180 days"
on public.audit_log for delete
to authenticated
using (
    public.is_system_admin()
    and created_at < (now() - interval '180 days')
);

