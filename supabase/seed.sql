-- =========================================================================
-- WARNING: This seed script is for LOCAL DEVELOPMENT ONLY.
-- Do NOT run this script on Production or Staging databases.
-- Supabase CLI only executes supabase/seed.sql locally during
-- 'supabase start' or 'supabase db reset'.
-- =========================================================================

-- Seed local development users and roles
-- Enable pgcrypto for password hashing
create extension if not exists "pgcrypto";

-- Clean up any existing seed data (optional, but helpful for clean runs)
delete from auth.users where email in ('admin@example.com', 'manager@example.com');

do $$
declare
    v_admin_id uuid := 'a1111111-1111-1111-1111-111111111111';
    v_manager_id uuid := 'b2222222-2222-2222-2222-222222222222';
    v_admin_email text := 'admin@example.com';
    v_manager_email text := 'manager@example.com';
    v_admin_pwd text := 'adminpassword';
    v_manager_pwd text := 'managerpassword';
begin
    -- 1. Create System Administrator Auth User
    insert into auth.users (
        id,
        instance_id,
        aud,
        role,
        email,
        encrypted_password,
        email_confirmed_at,
        raw_app_meta_data,
        raw_user_meta_data,
        created_at,
        updated_at,
        confirmation_token,
        recovery_token,
        email_change_token_new,
        email_change,
        phone_change_token,
        email_change_token_current,
        reauthentication_token
    ) values (
        v_admin_id,
        '00000000-0000-0000-0000-000000000000',
        'authenticated',
        'authenticated',
        v_admin_email,
        crypt(v_admin_pwd, gen_salt('bf')),
        now(),
        '{"provider":"email","providers":["email"]}',
        '{"full_name": "System Admin"}',
        now(),
        now(),
        '',
        '',
        '',
        '',
        '',
        '',
        ''
    );

    insert into auth.identities (
        id,
        user_id,
        provider_id,
        identity_data,
        provider,
        last_sign_in_at,
        created_at,
        updated_at
    ) values (
        v_admin_id,
        v_admin_id,
        v_admin_id,
        format('{"sub": "%s", "email": "%s"}', v_admin_id::text, v_admin_email)::jsonb,
        'email',
        now(),
        now(),
        now()
    );

    -- 2. Create Program Manager Auth User
    insert into auth.users (
        id,
        instance_id,
        aud,
        role,
        email,
        encrypted_password,
        email_confirmed_at,
        raw_app_meta_data,
        raw_user_meta_data,
        created_at,
        updated_at,
        confirmation_token,
        recovery_token,
        email_change_token_new,
        email_change,
        phone_change_token,
        email_change_token_current,
        reauthentication_token
    ) values (
        v_manager_id,
        '00000000-0000-0000-0000-000000000000',
        'authenticated',
        'authenticated',
        v_manager_email,
        crypt(v_manager_pwd, gen_salt('bf')),
        now(),
        '{"provider":"email","providers":["email"]}',
        '{"full_name": "Program Manager"}',
        now(),
        now(),
        '',
        '',
        '',
        '',
        '',
        '',
        ''
    );

    insert into auth.identities (
        id,
        user_id,
        provider_id,
        identity_data,
        provider,
        last_sign_in_at,
        created_at,
        updated_at
    ) values (
        v_manager_id,
        v_manager_id,
        v_manager_id,
        format('{"sub": "%s", "email": "%s"}', v_manager_id::text, v_manager_email)::jsonb,
        'email',
        now(),
        now(),
        now()
    );

    -- 3. Update the automatically created user_profile rows with the correct user_types.
    -- (The on_auth_user_created trigger automatically provisions the rows as 'Project Stakeholder').
    update public.user_profile
    set user_type = 'System Administrator'
    where auth_user_id = v_admin_id;

    update public.user_profile
    set user_type = 'Program Manager'
    where auth_user_id = v_manager_id;

end $$;
