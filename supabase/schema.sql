-- 내 계획표: 계정마다 자기 데이터만 보이는 저장소
-- Supabase 대시보드 → SQL Editor 에 이 내용을 그대로 붙여넣고 Run

create table if not exists public.docs (
  user_id    uuid        not null default auth.uid() references auth.users (id) on delete cascade,
  path       text        not null,          -- 예: schedule.json, plans/month/2026-11.md
  content    text        not null,
  updated_at timestamptz not null default now(),
  primary key (user_id, path)
);

-- 행 단위 보안: 로그인한 사람은 자기 user_id 행만 읽고 쓸 수 있음
alter table public.docs enable row level security;

drop policy if exists "docs: 내 것만 읽기" on public.docs;
drop policy if exists "docs: 내 것만 추가" on public.docs;
drop policy if exists "docs: 내 것만 수정" on public.docs;
drop policy if exists "docs: 내 것만 삭제" on public.docs;

create policy "docs: 내 것만 읽기" on public.docs for select to authenticated using (auth.uid() = user_id);
create policy "docs: 내 것만 추가" on public.docs for insert to authenticated with check (auth.uid() = user_id);
create policy "docs: 내 것만 수정" on public.docs for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "docs: 내 것만 삭제" on public.docs for delete to authenticated using (auth.uid() = user_id);

-- 로그인 안 한 사람(anon)은 아무것도 못 봄
revoke all on public.docs from anon;
grant select, insert, update, delete on public.docs to authenticated;
