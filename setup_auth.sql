-- ============================================================
-- 削減アミダクジ 運営ツール — 承認制ログイン用 SQL セットアップ
-- 実行先: Supabase Dashboard → SQL Editor (puzzliar's Project)
-- ============================================================
-- 実行内容:
--   1. user_approvals テーブル作成
--   2. dai@puzzliar.jp を管理者として初期投入
--   3. user_approvals の RLS ポリシー設定
--   4. amida_sessions / amida_period_logs の RLS を「承認済みユーザーのみ」に
-- ============================================================

-- ─── 1. user_approvals テーブル ───
create table if not exists public.user_approvals (
  id          uuid          primary key default gen_random_uuid(),
  email       text          unique not null,
  status      text          not null default 'pending'
              check (status in ('pending','approved','rejected')),
  is_admin    boolean       not null default false,
  requested_at timestamptz  not null default now(),
  approved_at timestamptz,
  approved_by text,
  notes       text
);

create index if not exists idx_user_approvals_email on public.user_approvals(email);
create index if not exists idx_user_approvals_status on public.user_approvals(status);

-- ─── 2. 初期管理者投入 ───
insert into public.user_approvals (email, status, is_admin, approved_at, approved_by, notes)
values ('dai@puzzliar.jp', 'approved', true, now(), 'system', '初期管理者')
on conflict (email) do update set
  status = 'approved',
  is_admin = true,
  approved_at = excluded.approved_at,
  notes = '初期管理者（再投入）';

-- ─── 3. user_approvals の RLS ───
alter table public.user_approvals enable row level security;

-- 既存ポリシーがあれば削除（冪等）
drop policy if exists "Read own approval row" on public.user_approvals;
drop policy if exists "Admins read all approvals" on public.user_approvals;
drop policy if exists "Self insert pending" on public.user_approvals;
drop policy if exists "Admin update approvals" on public.user_approvals;

-- 自分のレコードを読める（未承認でも自分の status は確認できる）
create policy "Read own approval row"
  on public.user_approvals
  for select to authenticated
  using ( lower(email) = lower(auth.jwt() ->> 'email') );

-- 管理者は全レコード読める
create policy "Admins read all approvals"
  on public.user_approvals
  for select to authenticated
  using ( exists (
    select 1 from public.user_approvals me
    where lower(me.email) = lower(auth.jwt() ->> 'email')
      and me.status = 'approved'
      and me.is_admin = true
  ) );

-- 自分の email で「pending」レコードを作れる（申請）
create policy "Self insert pending"
  on public.user_approvals
  for insert to authenticated
  with check (
    lower(email) = lower(auth.jwt() ->> 'email')
    and status = 'pending'
    and is_admin = false
  );

-- 管理者は他人の status を更新できる
create policy "Admin update approvals"
  on public.user_approvals
  for update to authenticated
  using ( exists (
    select 1 from public.user_approvals me
    where lower(me.email) = lower(auth.jwt() ->> 'email')
      and me.status = 'approved'
      and me.is_admin = true
  ) )
  with check ( true );

-- ─── 4. amida_sessions の RLS（承認済みユーザーのみ） ───
alter table public.amida_sessions enable row level security;

drop policy if exists "Approved users full access amida_sessions" on public.amida_sessions;

create policy "Approved users full access amida_sessions"
  on public.amida_sessions
  for all to authenticated
  using ( exists (
    select 1 from public.user_approvals
    where lower(email) = lower(auth.jwt() ->> 'email')
      and status = 'approved'
  ) )
  with check ( exists (
    select 1 from public.user_approvals
    where lower(email) = lower(auth.jwt() ->> 'email')
      and status = 'approved'
  ) );

-- ─── 5. amida_period_logs の RLS（同上） ───
alter table public.amida_period_logs enable row level security;

drop policy if exists "Approved users full access amida_period_logs" on public.amida_period_logs;

create policy "Approved users full access amida_period_logs"
  on public.amida_period_logs
  for all to authenticated
  using ( exists (
    select 1 from public.user_approvals
    where lower(email) = lower(auth.jwt() ->> 'email')
      and status = 'approved'
  ) )
  with check ( exists (
    select 1 from public.user_approvals
    where lower(email) = lower(auth.jwt() ->> 'email')
      and status = 'approved'
  ) );

-- ─── 確認クエリ ───
-- 管理者投入確認:
--   select * from public.user_approvals;
-- RLS 適用状態:
--   select tablename, rowsecurity from pg_tables
--   where schemaname='public' and tablename in
--     ('user_approvals','amida_sessions','amida_period_logs');
