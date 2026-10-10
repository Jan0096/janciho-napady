-- Development seed: one company, 4 users (admin, manager, 2 drivers).
-- Vehicles and reservations are added in later steps.
--
-- Local Supabase (`npx supabase start`): all e-mails are caught by Mailpit at http://localhost:54324,
-- so these fake addresses work for magic-link login.
-- Never run this on a production project.

insert into auth.users (
  instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
  raw_app_meta_data, raw_user_meta_data, created_at, updated_at,
  confirmation_token, recovery_token, email_change_token_new, email_change
)
select
  '00000000-0000-0000-0000-000000000000', u.id, 'authenticated', 'authenticated', u.email, '', now(),
  '{"provider":"email","providers":["email"]}', '{}', now(), now(),
  '', '', '', ''
from (values
  ('00000000-0000-4000-8000-000000000001'::uuid, 'admin@firma.test'),
  ('00000000-0000-4000-8000-000000000002'::uuid, 'spravca@firma.test'),
  ('00000000-0000-4000-8000-000000000003'::uuid, 'vodic1@firma.test'),
  ('00000000-0000-4000-8000-000000000004'::uuid, 'vodic2@firma.test')
) as u (id, email);

insert into auth.identities (id, user_id, provider_id, provider, identity_data, last_sign_in_at, created_at, updated_at)
select gen_random_uuid(), u.id, u.id::text, 'email',
  jsonb_build_object('sub', u.id::text, 'email', u.email, 'email_verified', true),
  now(), now(), now()
from auth.users u
where u.email like '%@firma.test';

insert into public.organizations (id, name)
values ('10000000-0000-4000-8000-000000000001', 'Testovacia firma s.r.o.');

insert into public.profiles (id, organization_id, role, full_name, phone, email) values
  ('00000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', 'admin',   'Anna Adminová',   '+421900000001', 'admin@firma.test'),
  ('00000000-0000-4000-8000-000000000002', '10000000-0000-4000-8000-000000000001', 'manager', 'Peter Správca',   '+421900000002', 'spravca@firma.test'),
  ('00000000-0000-4000-8000-000000000003', '10000000-0000-4000-8000-000000000001', 'driver',  'Jana Vodičová',   '+421900000003', 'vodic1@firma.test'),
  ('00000000-0000-4000-8000-000000000004', '10000000-0000-4000-8000-000000000001', 'driver',  'Marek Vodič',     '+421900000004', 'vodic2@firma.test');

-- One open invitation, so the onboarding flow can be tried with nova@firma.test.
insert into public.invitations (organization_id, email, role, invited_by)
values ('10000000-0000-4000-8000-000000000001', 'nova@firma.test', 'driver', '00000000-0000-4000-8000-000000000001');
