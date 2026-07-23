-- Migration to create organization_key, organization, and organization_internal tables.
-- organization_key provides an indirection layer mapping a UUID to a user-specified unique import_key.
-- organization contains the public organization metadata, linked to organization_key.
-- organization_internal contains private metadata (notes and overhead rates) with restricted permissions.

-- 1. Create organization_key table
create table public.organization_key (
    id uuid primary key default gen_random_uuid(),
    import_key text not null unique,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    created_by_user_id uuid references public.user_profile(id) on delete set null,
    updated_by_user_id uuid references public.user_profile(id) on delete set null
);

-- Indexing for organization_key
create index idx_organization_key_import_key on public.organization_key(import_key);

-- Trigger for organization_key updated_at
create trigger update_organization_key_updated_at
    before update on public.organization_key
    for each row
    execute function public.update_updated_at_column();

-- Enable RLS for organization_key
alter table public.organization_key enable row level security;
grant select, insert, update, delete on table public.organization_key to authenticated, service_role;

-- RLS Policies for organization_key (Anyone can read, only admin can write)
create policy "Allow select for anyone"
on public.organization_key for select
using (true);

create policy "Allow insert for admin only"
on public.organization_key for insert
to authenticated
with check (public.is_system_admin());

create policy "Allow update for admin only"
on public.organization_key for update
to authenticated
using (public.is_system_admin())
with check (public.is_system_admin());

create policy "Allow delete for admin only"
on public.organization_key for delete
to authenticated
using (public.is_system_admin());


-- 2. Create organization table
create table public.organization (
    id uuid primary key references public.organization_key(id) on delete cascade,
    organization_name text not null,
    organization_slug text not null unique,
    status text not null check (status in (
        'Active',
        'Inactive',
        'Archived',
        'Dormant',
        'Closed'
    )),
    organization_type text not null check (organization_type in (
        'Fiscal Sponsorship',
        'Event'
    )),
    description text,
    website_url text,
    source_code_url text,
    donation_url text,
    join_date date,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    created_by_user_id uuid references public.user_profile(id) on delete set null,
    updated_by_user_id uuid references public.user_profile(id) on delete set null,
    deleted_at timestamp with time zone,
    deleted_by_user_id uuid references public.user_profile(id) on delete set null
);

-- Indexing for organization
create index idx_organization_deleted_at on public.organization(deleted_at) where deleted_at is null;
create index idx_organization_status on public.organization(status);
create index idx_organization_created_by on public.organization(created_by_user_id);
create index idx_organization_updated_by on public.organization(updated_by_user_id);

-- Trigger for organization updated_at
create trigger update_organization_updated_at
    before update on public.organization
    for each row
    execute function public.update_updated_at_column();

-- Enable RLS for organization
alter table public.organization enable row level security;
grant select, insert, update, delete on table public.organization to authenticated, service_role;
grant select on table public.organization to anon;

-- RLS Policies for organization (Anyone can read, only admin can write)
create policy "Allow select for anyone"
on public.organization for select
using (true);

create policy "Allow insert for admin only"
on public.organization for insert
to authenticated
with check (public.is_system_admin());

create policy "Allow update for admin only"
on public.organization for update
to authenticated
using (public.is_system_admin())
with check (public.is_system_admin());

create policy "Allow delete for admin only"
on public.organization for delete
to authenticated
using (public.is_system_admin());


-- 3. Create organization_internal table
create table public.organization_internal (
    id uuid primary key references public.organization(id) on delete cascade,
    overhead_grant numeric not null default 0.0 check (overhead_grant >= 0),
    overhead_donation_general numeric not null default 0.0 check (overhead_donation_general >= 0),
    overhead_donation_corporate numeric not null default 0.0 check (overhead_donation_corporate >= 0),
    notes text,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    created_by_user_id uuid references public.user_profile(id) on delete set null,
    updated_by_user_id uuid references public.user_profile(id) on delete set null,
    deleted_at timestamp with time zone,
    deleted_by_user_id uuid references public.user_profile(id) on delete set null
);

-- Indexing for organization_internal
create index idx_organization_internal_deleted_at on public.organization_internal(deleted_at) where deleted_at is null;
create index idx_organization_internal_created_by on public.organization_internal(created_by_user_id);
create index idx_organization_internal_updated_by on public.organization_internal(updated_by_user_id);

-- Trigger for organization_internal updated_at
create trigger update_organization_internal_updated_at
    before update on public.organization_internal
    for each row
    execute function public.update_updated_at_column();

-- Enable RLS for organization_internal
alter table public.organization_internal enable row level security;
grant select, insert, update, delete on table public.organization_internal to authenticated, service_role;

-- RLS Policies for organization_internal (Only admin/manager can read/write)
create policy "Allow select for admin or manager"
on public.organization_internal for select
to authenticated
using (public.is_admin_or_manager());

create policy "Allow insert for admin only"
on public.organization_internal for insert
to authenticated
with check (public.is_system_admin());

create policy "Allow update for admin or manager"
on public.organization_internal for update
to authenticated
using (public.is_admin_or_manager())
with check (public.is_admin_or_manager());

create policy "Allow delete for admin only"
on public.organization_internal for delete
to authenticated
using (public.is_system_admin());
