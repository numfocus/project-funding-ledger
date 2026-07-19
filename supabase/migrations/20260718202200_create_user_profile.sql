-- Migration to create the user_profile table as specified in the Architecture Design.

-- Create user_profile table
create table public.user_profile (
    id uuid primary key default gen_random_uuid(),
    auth_user_id uuid not null unique references auth.users(id) on delete cascade,
    full_name text not null,
    email text not null,
    user_type text not null check (user_type in (
        'System Administrator',
        'Program Manager',
        'Organization Stakeholder'
    )),
    status text not null check (status in (
        'Active',
        'Invited',
        'Inactive',
        'Suspended'
    )),
    last_login_at timestamp with time zone,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    created_by_user_id uuid references public.user_profile(id) on delete set null,
    updated_by_user_id uuid references public.user_profile(id) on delete set null,
    deleted_at timestamp with time zone,
    deleted_by_user_id uuid references public.user_profile(id) on delete set null
);

-- Indexing strategy for user_profile to support auth lookups and joins
create index idx_user_profile_auth_user_id on public.user_profile(auth_user_id);
create index idx_user_profile_email on public.user_profile(email);
create index idx_user_profile_deleted_at on public.user_profile(deleted_at) where deleted_at is null;

-- Trigger to automatically update updated_at
create or replace function public.update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger update_user_profile_updated_at
    before update on public.user_profile
    for each row
    execute function public.update_updated_at_column();

-- Enable Row-Level Security
alter table public.user_profile enable row level security;

-- Grant permissions to standard roles
grant select, insert, update, delete on table public.user_profile to authenticated, service_role;

-- Helper functions for RLS to prevent recursion
create or replace function public.is_admin_or_manager()
returns boolean as $$
begin
    return exists (
        select 1 from public.user_profile
        where auth_user_id = auth.uid()
          and user_type in ('System Administrator', 'Program Manager')
          and deleted_at is null
          and status = 'Active'
    );
end;
$$ language plpgsql security definer set search_path = public;

create or replace function public.is_system_admin()
returns boolean as $$
begin
    return exists (
        select 1 from public.user_profile
        where auth_user_id = auth.uid()
          and user_type = 'System Administrator'
          and deleted_at is null
          and status = 'Active'
    );
end;
$$ language plpgsql security definer set search_path = public;

-- RLS Policies
create policy "Allow select for self or admin/manager"
on public.user_profile for select
using (
    auth.uid() = auth_user_id
    or public.is_admin_or_manager()
);

create policy "Allow insert for admin only"
on public.user_profile for insert
with check (
    public.is_system_admin()
);

create policy "Allow update for self or admin"
on public.user_profile for update
using (
    auth.uid() = auth_user_id
    or public.is_system_admin()
)
with check (
    auth.uid() = auth_user_id
    or public.is_system_admin()
);

create policy "Allow delete for admin only"
on public.user_profile for delete
using (
    public.is_system_admin()
);

-- Trigger to prevent non-admins from changing their own user_type or status
create or replace function public.check_profile_update()
returns trigger as $$
begin
    if (old.auth_user_id = auth.uid() and not public.is_system_admin()) then
        if (new.user_type <> old.user_type or new.status <> old.status) then
            raise exception 'Unauthorized to change user_type or status';
        end if;
    end if;
    return new;
end;
$$ language plpgsql;

create trigger check_user_profile_update
    before update on public.user_profile
    for each row
    execute function public.check_profile_update();

