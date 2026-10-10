-- Phase 1, step 1: organizations, user profiles with roles, invitations.
--
-- Security model:
--   * Every tenant table carries organization_id and has RLS enabled.
--   * Clients may only SELECT through RLS; all writes that touch roles,
--     membership or invitations go through SECURITY DEFINER functions
--     below, which validate the caller's role inside the database.
--   * A deactivated profile behaves like "no organization" (sees nothing).

create type public.user_role as enum ('admin', 'manager', 'driver');

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

create table public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(btrim(name)) between 2 and 200),
  -- Company-wide settings (reservation approval, private trip rules, season dates, ...).
  settings jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  organization_id uuid not null references public.organizations (id) on delete restrict,
  role public.user_role not null default 'driver',
  full_name text not null check (char_length(btrim(full_name)) between 2 and 200),
  phone text check (phone is null or char_length(phone) <= 40),
  -- Copy of the login e-mail so admins can see who is who without reading auth.users.
  email text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index profiles_organization_id_idx on public.profiles (organization_id);

create table public.invitations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations (id) on delete cascade,
  email text not null check (email = lower(btrim(email)) and email like '%_@_%'),
  role public.user_role not null,
  invited_by uuid references public.profiles (id) on delete set null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '14 days',
  accepted_at timestamptz,
  accepted_by uuid references auth.users (id) on delete set null,
  revoked_at timestamptz
);

-- At most one open invitation per e-mail within a company.
create unique index invitations_open_email_idx
  on public.invitations (organization_id, email)
  where accepted_at is null and revoked_at is null;

create index invitations_email_idx on public.invitations (email);

-- ---------------------------------------------------------------------------
-- Helpers used by RLS policies (SECURITY DEFINER avoids recursive RLS on profiles)
-- ---------------------------------------------------------------------------

create function public.current_organization_id()
returns uuid
language sql
stable
security definer
set search_path = ''
as $$
  select p.organization_id
  from public.profiles p
  where p.id = auth.uid() and p.is_active
$$;

create function public.current_user_role()
returns public.user_role
language sql
stable
security definer
set search_path = ''
as $$
  select p.role
  from public.profiles p
  where p.id = auth.uid() and p.is_active
$$;

create function public.current_user_email()
returns text
language sql
stable
set search_path = ''
as $$
  select lower(btrim(auth.jwt() ->> 'email'))
$$;

create function public.touch_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create trigger profiles_touch_updated_at
  before update on public.profiles
  for each row execute function public.touch_updated_at();

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------

alter table public.organizations enable row level security;
alter table public.profiles enable row level security;
alter table public.invitations enable row level security;

-- Clients get no direct write access except the explicitly granted columns below.
revoke all on public.organizations, public.profiles, public.invitations from anon, authenticated;
grant select on public.organizations, public.profiles, public.invitations to authenticated;
grant update (name) on public.organizations to authenticated;
grant update (full_name, phone) on public.profiles to authenticated;

-- organizations
create policy "members read own organization"
  on public.organizations for select to authenticated
  using (id = public.current_organization_id());

create policy "admins rename own organization"
  on public.organizations for update to authenticated
  using (id = public.current_organization_id() and public.current_user_role() = 'admin')
  with check (id = public.current_organization_id());

-- profiles
create policy "members read colleagues"
  on public.profiles for select to authenticated
  using (organization_id = public.current_organization_id() or id = auth.uid());

create policy "users edit own contact details"
  on public.profiles for update to authenticated
  using (id = auth.uid() and is_active)
  with check (id = auth.uid());

-- invitations
create policy "admins read company invitations"
  on public.invitations for select to authenticated
  using (organization_id = public.current_organization_id() and public.current_user_role() = 'admin');

-- ---------------------------------------------------------------------------
-- RPC: onboarding
-- ---------------------------------------------------------------------------

-- Creates a new company and makes the caller its admin.
create function public.create_organization(p_name text, p_full_name text)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_email text := public.current_user_email();
  v_org_id uuid;
begin
  if v_uid is null or v_email is null then
    raise exception 'not_authenticated' using errcode = '28000';
  end if;
  if exists (select 1 from public.profiles where id = v_uid) then
    raise exception 'already_member' using errcode = 'P0001';
  end if;

  insert into public.organizations (name) values (btrim(p_name))
  returning id into v_org_id;

  insert into public.profiles (id, organization_id, role, full_name, email)
  values (v_uid, v_org_id, 'admin', btrim(p_full_name), v_email);

  return v_org_id;
end;
$$;

-- Open invitations for the signed-in user's e-mail (used before they have a profile).
create function public.my_pending_invitations()
returns table (id uuid, organization_name text, role public.user_role, expires_at timestamptz)
language sql
stable
security definer
set search_path = ''
as $$
  select i.id, o.name, i.role, i.expires_at
  from public.invitations i
  join public.organizations o on o.id = i.organization_id
  where i.email = public.current_user_email()
    and i.accepted_at is null
    and i.revoked_at is null
    and i.expires_at > now()
  order by i.created_at desc
$$;

create function public.accept_invitation(p_invitation_id uuid, p_full_name text)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_email text := public.current_user_email();
  v_inv public.invitations;
begin
  if v_uid is null or v_email is null then
    raise exception 'not_authenticated' using errcode = '28000';
  end if;
  if exists (select 1 from public.profiles where id = v_uid) then
    raise exception 'already_member' using errcode = 'P0001';
  end if;

  select * into v_inv
  from public.invitations
  where id = p_invitation_id
    and email = v_email
    and accepted_at is null
    and revoked_at is null
    and expires_at > now()
  for update;

  if not found then
    raise exception 'invitation_not_found' using errcode = 'P0002';
  end if;

  insert into public.profiles (id, organization_id, role, full_name, email)
  values (v_uid, v_inv.organization_id, v_inv.role, btrim(p_full_name), v_email);

  update public.invitations
  set accepted_at = now(), accepted_by = v_uid
  where id = v_inv.id;

  return v_inv.organization_id;
end;
$$;

-- ---------------------------------------------------------------------------
-- RPC: user management (admin only)
-- ---------------------------------------------------------------------------

create function public.assert_admin()
returns uuid
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_org uuid := public.current_organization_id();
begin
  if v_org is null or public.current_user_role() is distinct from 'admin' then
    raise exception 'forbidden' using errcode = '42501';
  end if;
  return v_org;
end;
$$;

create function public.create_invitation(p_email text, p_role public.user_role)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_org uuid := public.assert_admin();
  v_email text := lower(btrim(p_email));
  v_id uuid;
begin
  if exists (select 1 from public.profiles where organization_id = v_org and email = v_email) then
    raise exception 'already_member' using errcode = 'P0001';
  end if;

  -- Re-inviting replaces the previous open invitation (new role, new expiry).
  update public.invitations
  set revoked_at = now()
  where organization_id = v_org and email = v_email
    and accepted_at is null and revoked_at is null;

  insert into public.invitations (organization_id, email, role, invited_by)
  values (v_org, v_email, p_role, auth.uid())
  returning id into v_id;

  return v_id;
end;
$$;

create function public.revoke_invitation(p_invitation_id uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_org uuid := public.assert_admin();
begin
  update public.invitations
  set revoked_at = now()
  where id = p_invitation_id and organization_id = v_org
    and accepted_at is null and revoked_at is null;
  if not found then
    raise exception 'invitation_not_found' using errcode = 'P0002';
  end if;
end;
$$;

-- Raises if the change would leave the company without an active admin.
create function public.assert_not_last_admin(p_org uuid, p_user_id uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if not exists (
    select 1 from public.profiles
    where organization_id = p_org and role = 'admin' and is_active and id <> p_user_id
  ) then
    raise exception 'last_admin' using errcode = 'P0001';
  end if;
end;
$$;

create function public.set_member_role(p_user_id uuid, p_role public.user_role)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_org uuid := public.assert_admin();
  v_current public.user_role;
begin
  select role into v_current
  from public.profiles
  where id = p_user_id and organization_id = v_org
  for update;
  if not found then
    raise exception 'member_not_found' using errcode = 'P0002';
  end if;

  if v_current = 'admin' and p_role <> 'admin' then
    perform public.assert_not_last_admin(v_org, p_user_id);
  end if;

  update public.profiles set role = p_role where id = p_user_id;
end;
$$;

create function public.set_member_active(p_user_id uuid, p_active boolean)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_org uuid := public.assert_admin();
  v_role public.user_role;
begin
  select role into v_role
  from public.profiles
  where id = p_user_id and organization_id = v_org
  for update;
  if not found then
    raise exception 'member_not_found' using errcode = 'P0002';
  end if;

  if not p_active and v_role = 'admin' then
    perform public.assert_not_last_admin(v_org, p_user_id);
  end if;

  update public.profiles set is_active = p_active where id = p_user_id;
end;
$$;

-- Functions are callable only by signed-in users; internal helpers not at all.
revoke execute on all functions in schema public from public, anon;
grant execute on function
  public.current_organization_id(),
  public.current_user_role(),
  public.create_organization(text, text),
  public.my_pending_invitations(),
  public.accept_invitation(uuid, text),
  public.create_invitation(text, public.user_role),
  public.revoke_invitation(uuid),
  public.set_member_role(uuid, public.user_role),
  public.set_member_active(uuid, boolean)
to authenticated;
revoke execute on function
  public.assert_admin(),
  public.assert_not_last_admin(uuid, uuid),
  public.touch_updated_at()
from authenticated;
