-- Tenant isolation, roles and invitation flow.
-- Runs after migrations + seed; everything is rolled back at the end.
-- Run: npm run test:db

begin;

create schema tests;
grant usage on schema tests to anon, authenticated;

create function tests.check(ok boolean, label text) returns void language plpgsql as $$
begin
  if ok is distinct from true then
    raise exception 'FAILED: %', label;
  end if;
  raise notice 'ok - %', label;
end $$;

-- Runs sql and expects it to fail with an error message containing `expected`.
create function tests.throws(sql text, expected text, label text) returns void language plpgsql as $$
begin
  begin
    execute sql;
  exception when others then
    if position(expected in sqlerrm) > 0 then
      raise notice 'ok - %', label;
      return;
    end if;
    raise exception 'FAILED: % (expected "%", got "%")', label, expected, sqlerrm;
  end;
  raise exception 'FAILED: % (expected error "%", got none)', label, expected;
end $$;

-- Number of rows affected by a statement (to prove RLS silently filtered a write).
create function tests.affected(sql text) returns bigint language plpgsql as $$
declare n bigint;
begin
  execute sql;
  get diagnostics n = row_count;
  return n;
end $$;

grant execute on all functions in schema tests to anon, authenticated;

-- Acting as a user = role "authenticated" + JWT claims, like PostgREST does.
create function tests.act_as(p_sub text, p_email text) returns void language sql as $$
  select set_config('request.jwt.claims', json_build_object('sub', p_sub, 'email', p_email)::text, true);
$$;

-- ---------------------------------------------------------------------------
-- Fixtures: a second company "B" with its own admin, and users without a company.
-- ---------------------------------------------------------------------------
insert into auth.users (id, email) values
  ('20000000-0000-4000-8000-000000000001', 'admin@other.test'),
  ('30000000-0000-4000-8000-000000000001', 'nova@firma.test'),
  ('30000000-0000-4000-8000-000000000002', 'cudzi@niekde.test');
insert into public.organizations (id, name) values ('20000000-0000-4000-8000-0000000000aa', 'Iná firma a.s.');
insert into public.profiles (id, organization_id, role, full_name, email)
values ('20000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-0000000000aa', 'admin', 'Boris Iný', 'admin@other.test');
insert into public.invitations (organization_id, email, role, expires_at)
values ('20000000-0000-4000-8000-0000000000aa', 'expired@niekde.test', 'driver', now() - interval '1 day');

-- ---------------------------------------------------------------------------
-- Anonymous visitors see nothing and cannot call RPCs.
-- ---------------------------------------------------------------------------
set local role anon;
select tests.throws('select * from public.profiles', 'permission denied', 'anon cannot read profiles');
select tests.throws('select public.create_organization(''X firma'', ''X Y'')', 'permission denied', 'anon cannot create organization');
reset role;

-- ---------------------------------------------------------------------------
-- Driver of company A
-- ---------------------------------------------------------------------------
set local role authenticated;
select tests.act_as('00000000-0000-4000-8000-000000000003', 'vodic1@firma.test');

select tests.check((select count(*) from public.profiles) = 4, 'driver sees the 4 colleagues of company A');
select tests.check(not exists (select 1 from public.profiles where email = 'admin@other.test'), 'driver does not see company B users');
select tests.check((select count(*) from public.organizations) = 1, 'driver sees only own organization');
select tests.check((select count(*) from public.invitations) = 0, 'driver does not see invitations');
select tests.check(tests.affected('update public.profiles set phone = ''+421911111111'' where id = auth.uid()') = 1, 'driver can edit own phone');
select tests.throws('update public.profiles set role = ''admin'' where id = auth.uid()', 'permission denied', 'driver cannot change own role');
select tests.throws('update public.profiles set organization_id = ''20000000-0000-4000-8000-0000000000aa'' where id = auth.uid()', 'permission denied', 'driver cannot move to another company');
select tests.check(tests.affected('update public.profiles set full_name = ''Hacker'' where id <> auth.uid()') = 0, 'driver cannot edit colleagues');
select tests.check(tests.affected('update public.organizations set name = ''Hacked''') = 0, 'driver cannot rename company');
select tests.throws('insert into public.profiles (id, organization_id, full_name, email) values (gen_random_uuid(), ''20000000-0000-4000-8000-0000000000aa'', ''Xx'', ''x@x.test'')', 'permission denied', 'driver cannot insert profiles');
select tests.throws('delete from public.profiles', 'permission denied', 'driver cannot delete profiles');
select tests.throws('select public.create_invitation(''x@firma.test'', ''driver'')', 'forbidden', 'driver cannot invite');
select tests.throws('select public.set_member_role(''00000000-0000-4000-8000-000000000003'', ''admin'')', 'forbidden', 'driver cannot promote self');
select tests.throws('select public.create_organization(''Druhá firma'', ''Jana'')', 'already_member', 'member cannot create another company');
select tests.throws('select public.assert_admin()', 'permission denied', 'internal helper is not callable');
reset role;

-- Manager is not an admin either.
set local role authenticated;
select tests.act_as('00000000-0000-4000-8000-000000000002', 'spravca@firma.test');
select tests.throws('select public.create_invitation(''x@firma.test'', ''driver'')', 'forbidden', 'manager cannot invite');
select tests.check((select count(*) from public.invitations) = 0, 'manager does not see invitations');
reset role;

-- ---------------------------------------------------------------------------
-- Admin of company A
-- ---------------------------------------------------------------------------
set local role authenticated;
select tests.act_as('00000000-0000-4000-8000-000000000001', 'admin@firma.test');

select tests.check((select count(*) from public.invitations) = 1, 'admin sees own company invitations only');
select tests.check(public.create_invitation('  Novy.Vodic@Firma.test ', 'driver') is not null, 'admin can invite');
select tests.check(exists (select 1 from public.invitations where email = 'novy.vodic@firma.test'), 'invited e-mail is normalised');
select public.create_invitation('novy.vodic@firma.test', 'manager');
select tests.check(
  (select count(*) from public.invitations where email = 'novy.vodic@firma.test' and revoked_at is null) = 1
  and (select role from public.invitations where email = 'novy.vodic@firma.test' and revoked_at is null) = 'manager',
  're-invite replaces the open invitation');
select tests.throws('select public.create_invitation(''vodic2@firma.test'', ''driver'')', 'already_member', 'cannot invite an existing member');
select tests.throws('select public.set_member_role(''20000000-0000-4000-8000-000000000001'', ''driver'')', 'member_not_found', 'admin cannot touch company B users');
select tests.throws('select public.set_member_active(''20000000-0000-4000-8000-000000000001'', false)', 'member_not_found', 'admin cannot deactivate company B users');
select tests.throws('select public.set_member_role(auth.uid(), ''driver'')', 'last_admin', 'last admin cannot demote self');
select tests.throws('select public.set_member_active(auth.uid(), false)', 'last_admin', 'last admin cannot deactivate self');
select public.set_member_role('00000000-0000-4000-8000-000000000002', 'admin');
select tests.check((select role from public.profiles where id = '00000000-0000-4000-8000-000000000002') = 'admin', 'admin can promote manager');
select public.set_member_role('00000000-0000-4000-8000-000000000002', 'manager');
select tests.check(tests.affected('update public.organizations set name = ''Testovacia firma 2 s.r.o.''') = 1, 'admin can rename company');
select public.set_member_active('00000000-0000-4000-8000-000000000004', false);
reset role;

-- Deactivated driver loses access to company data.
set local role authenticated;
select tests.act_as('00000000-0000-4000-8000-000000000004', 'vodic2@firma.test');
select tests.check(public.current_organization_id() is null, 'deactivated user has no organization');
select tests.check((select count(*) from public.profiles) = 1, 'deactivated user sees only own profile');
select tests.check((select count(*) from public.organizations) = 0, 'deactivated user sees no company');
reset role;

-- ---------------------------------------------------------------------------
-- Admin of company B
-- ---------------------------------------------------------------------------
set local role authenticated;
select tests.act_as('20000000-0000-4000-8000-000000000001', 'admin@other.test');
select tests.check((select count(*) from public.profiles) = 1, 'company B admin sees only own company');
select tests.check(not exists (select 1 from public.invitations where email like '%@firma.test'), 'company B admin does not see company A invitations');
select tests.check(tests.affected('update public.organizations set name = ''Hacked'' where id = ''10000000-0000-4000-8000-000000000001''') = 0, 'company B admin cannot rename company A');
reset role;
select set_config('tests.inv_a', (select id::text from public.invitations where email = 'nova@firma.test'), true);
set local role authenticated;
select tests.throws(format('select public.revoke_invitation(%L)', current_setting('tests.inv_a')), 'invitation_not_found', 'company B admin cannot revoke company A invitation');
reset role;

-- ---------------------------------------------------------------------------
-- Invited newcomer (nova@firma.test has an invitation from the seed)
-- ---------------------------------------------------------------------------
set local role authenticated;
select tests.act_as('30000000-0000-4000-8000-000000000001', 'nova@firma.test');
select tests.check(public.current_organization_id() is null, 'newcomer has no organization yet');
select tests.check((select count(*) from public.profiles) = 0, 'newcomer sees no profiles');
select tests.check((select count(*) from public.my_pending_invitations()) = 1, 'newcomer sees own pending invitation');
select tests.throws('select public.accept_invitation(gen_random_uuid(), ''Nová Kolegyňa'')', 'invitation_not_found', 'unknown invitation is rejected');
select tests.check(
  public.accept_invitation((select id from public.my_pending_invitations() limit 1), 'Nová Kolegyňa') = '10000000-0000-4000-8000-000000000001',
  'newcomer accepts invitation');
select tests.check(public.current_user_role() = 'driver', 'newcomer gets the invited role');
select tests.check((select count(*) from public.profiles) = 5, 'newcomer now sees company A');
select tests.check((select count(*) from public.my_pending_invitations()) = 0, 'accepted invitation is no longer pending');
reset role;

-- ---------------------------------------------------------------------------
-- Stranger: cannot use someone else's invitation, can found own company.
-- ---------------------------------------------------------------------------
set local role authenticated;
select tests.act_as('30000000-0000-4000-8000-000000000002', 'cudzi@niekde.test');
select tests.check((select count(*) from public.my_pending_invitations()) = 0, 'stranger has no invitations');
reset role;
select set_config('tests.inv', (select id::text from public.invitations where email = 'novy.vodic@firma.test' and revoked_at is null), true);
select set_config('tests.expired', (select id::text from public.invitations where email = 'expired@niekde.test'), true);
set local role authenticated;
select tests.throws(format('select public.accept_invitation(%L, ''Cudzí'')', current_setting('tests.inv')), 'invitation_not_found', 'stranger cannot accept invitation for another e-mail');
select tests.act_as('30000000-0000-4000-8000-000000000002', 'expired@niekde.test');
select tests.throws(format('select public.accept_invitation(%L, ''Cudzí'')', current_setting('tests.expired')), 'invitation_not_found', 'expired invitation cannot be accepted');
select tests.act_as('30000000-0000-4000-8000-000000000002', 'cudzi@niekde.test');
select tests.check(public.create_organization('Cudzia firma', 'Cyril Cudzí') is not null, 'stranger founds own company');
select tests.check(public.current_user_role() = 'admin', 'founder becomes admin');
select tests.check((select count(*) from public.profiles) = 1, 'new company sees only its founder');
select tests.check((select count(*) from public.organizations) = 1, 'new company sees only itself');
reset role;

rollback;
