-- Migration to allow creating user profiles before registration and auto-linking auth.users

-- Drop the not null constraint on auth_user_id
alter table public.user_profile alter column auth_user_id drop not null;

-- Trigger to link auth_user_id on registration
create or replace function public.handle_new_auth_user()
returns trigger as $$
begin
    update public.user_profile
    set auth_user_id = new.id,
        status = 'Active',
        full_name = coalesce(nullif(new.raw_user_meta_data->>'full_name', ''), full_name)
    where email = new.email
      and auth_user_id is null;
      
    return new;
end;
$$ language plpgsql security definer;

-- Drop trigger if exists
drop trigger if exists on_auth_user_created on auth.users;

-- Create trigger on auth.users (in schema auth)
create trigger on_auth_user_created
    after insert on auth.users
    for each row
    execute function public.handle_new_auth_user();

-- RPC function to check if an email is invited/exists without auth_user_id
create or replace function public.is_email_invited(check_email text)
returns boolean as $$
begin
    return exists (
        select 1 from public.user_profile
        where email = check_email
          and auth_user_id is null
          and deleted_at is null
    );
end;
$$ language plpgsql security definer set search_path = public;
