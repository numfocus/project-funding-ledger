-- =========================================================================
-- WARNING: This seed script is for LOCAL DEVELOPMENT ONLY.
-- Do NOT run this script on Production or Staging databases.
-- Supabase CLI only executes supabase/seed.sql locally during
-- 'supabase start' or 'supabase db reset'.
-- =========================================================================
SET session_replication_role = replica;

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
        '{"full_name": "Oscar Seymore Slate"}',
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
        '{"full_name": "Fred Flintstone"}',
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

--
-- PostgreSQL database dump
--

-- \restrict dxOf8JrSW2zv1lwrTjlcVcwocswfhrAmJWAsAyUGwgLUMoCgmbTzQkVMdGpUck0

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: organization_key; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO "public"."organization_key" ("id", "import_key", "created_at", "updated_at", "created_by_user_id", "updated_by_user_id") VALUES
	('db1ff72a-4dbc-4aa5-ae93-235382df5682', 'Alpha', '2026-07-19 19:20:13.23782+00', '2026-07-19 19:20:13.23782+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c'),
	('165d6c2b-5859-408b-ab83-d6a0f2cf06a9', 'Alpha-Beta | Pandora', '2026-07-19 19:20:25.621172+00', '2026-07-19 19:20:25.621172+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c'),
	('25a245d8-42b5-40ee-9814-7a25829f214b', 'Beta | Ananke', '2026-07-19 19:20:41.462802+00', '2026-07-19 19:20:41.462802+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c'),
	('fe3a0786-5d5b-4450-a491-406fa4b62048', 'Delta', '2026-07-19 19:20:48.362317+00', '2026-07-19 19:20:48.362317+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c'),
	('93acbd22-24c9-449a-b9db-e4503e09b554', 'Epsilon', '2026-07-19 19:20:52.525516+00', '2026-07-19 19:20:52.525516+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c'),
	('66e06e5d-f53b-4a3f-9625-660700a83862', 'Eta', '2026-07-19 19:20:55.441291+00', '2026-07-19 19:20:55.441291+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c');

--
-- Data for Name: organization; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO "public"."organization" ("id", "organization_name", "organization_slug", "status", "organization_type", "description", "website_url", "source_code_url", "donation_url", "join_date", "created_at", "updated_at", "created_by_user_id", "updated_by_user_id", "deleted_at", "deleted_by_user_id") VALUES
	('db1ff72a-4dbc-4aa5-ae93-235382df5682', 'Alpha', 'alpha', 'Active', 'Fiscal Sponsorship', 'Alpha: Alpha proclaims that all the kingdoms of the earth may at last be tamed by Python''s gentle hand.', 'https://alpha.org/', 'https://github.com/alpha/alpha', 'https://numfocus.org/donate-for-alpha', '2016-02-11', '2026-07-19 19:20:13.243318+00', '2026-07-19 19:20:13.243318+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL),
	('165d6c2b-5859-408b-ab83-d6a0f2cf06a9', 'Alpha-Beta', 'alpha-beta', 'Active', 'Fiscal Sponsorship', 'Alpha-Beta | Pandora: Alpha-Beta | Pandora avers that open tools and shared knowledge are the surest companions of scientific progress.', 'https://www.alpha-beta-pandora.org/', 'https://github.com/alpha-beta-pandora/alpha-beta-pandora', 'https://numfocus.org/donate-to-alpha-beta-pandora', '2019-01-13', '2026-07-19 19:20:25.627751+00', '2026-07-19 19:20:25.627751+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL),
	('25a245d8-42b5-40ee-9814-7a25829f214b', 'Beta', 'beta', 'Active', 'Fiscal Sponsorship', 'Beta | Ananke: Beta | Ananke maintains that even the most unruly data may be brought into elegant and useful order.', 'https://www.beta-ananke.org/', 'https://github.com/beta-ananke/beta-ananke', 'https://numfocus.org/donate-to-beta-ananke', '2020-07-22', '2026-07-19 19:20:41.467123+00', '2026-07-19 19:20:41.467123+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL),
	('fe3a0786-5d5b-4450-a491-406fa4b62048', 'Delta', 'delta', 'Active', 'Fiscal Sponsorship', 'Iota: Iota maintains that the hidden workings of nature are but eager to reveal themselves to those who wield it wisely.', 'https://delta.org/', 'https://github.com/delta/delta', 'https://numfocus.org/donate-to-Delta', '2023-10-27', '2026-07-19 19:20:48.367804+00', '2026-07-19 19:20:48.367804+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL),
	('93acbd22-24c9-449a-b9db-e4503e09b554', 'Epsilon', 'epsilon', 'Active', 'Fiscal Sponsorship', 'Epsilon: Epsilon would have thee believe the very heavens themselves cannot be charted save through its noble design.', 'https://www.epsilon.org/', 'https://github.com/epsilon/epsilon', 'https://numfocus.org/donate-to-epsilon', '2014-09-17', '2026-07-19 19:20:52.531017+00', '2026-07-19 19:20:52.531017+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL),
	('66e06e5d-f53b-4a3f-9625-660700a83862', 'Eta', 'eta', 'Active', 'Fiscal Sponsorship', 'Eta: Eta would have thee think that all of scientific endeavor rests securely upon its steadfast shoulders.', 'https://eta.org/', 'https://github.com/eta/eta', 'https://numfocus.org/donate-to-eta', '2019-11-05', '2026-07-19 19:20:55.447429+00', '2026-07-19 19:20:55.447429+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL);

--
-- Data for Name: organization_internal; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO "public"."organization_internal" ("id", "overhead_grant", "overhead_donation_general", "overhead_donation_corporate", "notes", "created_at", "updated_at", "created_by_user_id", "updated_by_user_id", "deleted_at", "deleted_by_user_id") VALUES
	('db1ff72a-4dbc-4aa5-ae93-235382df5682', 0.15, 0.1, 0.1, NULL, '2026-07-19 19:20:13.247742+00', '2026-07-19 19:20:13.247742+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL),
	('165d6c2b-5859-408b-ab83-d6a0f2cf06a9', 0.15, 0.1, 0.1, NULL, '2026-07-19 19:20:25.633744+00', '2026-07-19 19:20:25.633744+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL),
	('25a245d8-42b5-40ee-9814-7a25829f214b', 0.15, 0.1, 0.1, NULL, '2026-07-19 19:20:41.471572+00', '2026-07-19 19:20:41.471572+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL),
	('fe3a0786-5d5b-4450-a491-406fa4b62048', 0.15, 0.1, 0.1, NULL, '2026-07-19 19:20:48.372209+00', '2026-07-19 19:20:48.372209+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL),
	('93acbd22-24c9-449a-b9db-e4503e09b554', 0.15, 0.1, 0.1, NULL, '2026-07-19 19:20:52.535172+00', '2026-07-19 19:20:52.535172+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL),
	('66e06e5d-f53b-4a3f-9625-660700a83862', 0.15, 0.1, 0.1, NULL, '2026-07-19 19:20:55.452006+00', '2026-07-19 19:20:55.452006+00', '33e5f4cd-d43a-4087-bade-e9e55365d08c', '33e5f4cd-d43a-4087-bade-e9e55365d08c', NULL, NULL);

--
-- PostgreSQL database dump complete
--

-- \unrestrict dxOf8JrSW2zv1lwrTjlcVcwocswfhrAmJWAsAyUGwgLUMoCgmbTzQkVMdGpUck0

RESET ALL;
