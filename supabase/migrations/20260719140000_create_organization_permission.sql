-- Migration to create organization_permission table and update RLS policies for organization access control.

-- 1. Create organization_permission table
create table public.organization_permission (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.user_profile(id) on delete cascade,
    organization_id uuid not null references public.organization(id) on delete cascade,
    permission_level text not null check (permission_level in ('View', 'Edit Metadata', 'Manage')),
    status text not null check (status in ('Active', 'Inactive', 'Revoked')),
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    created_by_user_id uuid references public.user_profile(id) on delete set null,
    revoked_at timestamp with time zone,
    revoked_by_user_id uuid references public.user_profile(id) on delete set null,
    notes text
);

-- Indexing strategy for organization_permission
create index idx_organization_permission_user_id on public.organization_permission(user_id);
create index idx_organization_permission_org_id on public.organization_permission(organization_id);
create index idx_organization_permission_status on public.organization_permission(status);

-- Unique constraint: prevent more than one active Permission record for the same User Profile and Organization
create unique index idx_organization_permission_active_unique 
    on public.organization_permission(user_id, organization_id) 
    where (status = 'Active');

-- Trigger to automatically update updated_at
create trigger update_organization_permission_updated_at
    before update on public.organization_permission
    for each row
    execute function public.update_updated_at_column();

-- Enable Row-Level Security
alter table public.organization_permission enable row level security;

-- Grant permissions to standard roles
grant select, insert, update, delete on table public.organization_permission to authenticated, service_role;

-- 2. Helper security function to check organization access (bypasses RLS recursion using security definer)
create or replace function public.has_organization_access(org_id uuid)
returns boolean as $$
begin
    -- 1. System Admins have access automatically
    if public.is_system_admin() then
        return true;
    end if;

    -- 2. Other active users must have an active permission record
    return exists (
        select 1 from public.organization_permission op
        join public.user_profile up on up.id = op.user_id
        where up.auth_user_id = auth.uid()
          and op.organization_id = org_id
          and op.status = 'Active'
          and up.deleted_at is null
          and up.status = 'Active'
    );
end;
$$ language plpgsql security definer set search_path = public;

-- 3. RLS Policies for organization_permission
create policy "Allow select for self or admin/manager"
on public.organization_permission for select
to authenticated
using (
    user_id in (select id from public.user_profile where auth_user_id = auth.uid())
    or public.is_admin_or_manager()
);

create policy "Allow insert for admin only"
on public.organization_permission for insert
to authenticated
with check (
    public.is_system_admin()
);

create policy "Allow update for admin only"
on public.organization_permission for update
to authenticated
using (
    public.is_system_admin()
)
with check (
    public.is_system_admin()
);

create policy "Allow delete for admin only"
on public.organization_permission for delete
to authenticated
using (
    public.is_system_admin()
);

-- 4. Update RLS Policies for existing organization table
drop policy if exists "Allow select for anyone" on public.organization;

create policy "Allow select for authorized users"
on public.organization for select
to authenticated
using (
    public.has_organization_access(id)
);

-- 5. Update RLS Policies for existing organization_internal table
drop policy if exists "Allow select for admin or manager" on public.organization_internal;

create policy "Allow select for authorized users"
on public.organization_internal for select
to authenticated
using (
    public.has_organization_access(id)
);
