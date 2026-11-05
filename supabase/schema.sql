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

-- 🔒 크기·이름 제한: 구글 계정만 있으면 누구나 로그인할 수 있어서,
-- 한 계정이 아주 큰 글이나 이상한 경로를 잔뜩 넣어 DB(무료 500MB)를 채우거나 알림 실행을 붙잡지 못하게 해요.
-- (not valid: 이미 있는 행은 검사하지 않고 새로 쓰는 것만 검사 → 여러 번 실행해도 안전)
alter table public.docs drop constraint if exists docs_path_ok;
alter table public.docs add constraint docs_path_ok check (
  char_length(path) between 1 and 200
  and path !~ '(^/|\\|(^|/)\.\.(/|$)|[[:cntrl:]])'   -- 절대경로, 역슬래시, .., 제어문자 금지
) not valid;
alter table public.docs drop constraint if exists docs_content_size;
alter table public.docs add constraint docs_content_size check (octet_length(content) <= 2000000) not valid;   -- 한 파일 2MB

-- 계정 하나에 파일 3000개까지
create or replace function public.docs_row_limit() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  -- upsert(이미 있는 파일 고치기)도 insert 로 들어오니, 새 파일일 때만 셈
  if not exists (select 1 from public.docs where user_id = new.user_id and path = new.path)
     and (select count(*) from public.docs where user_id = new.user_id) >= 3000 then
    raise exception '저장할 수 있는 파일 수(3000개)를 넘었어요' using errcode = '54000';
  end if;
  return new;
end $$;
revoke all on function public.docs_row_limit() from public, anon, authenticated;
drop trigger if exists docs_row_limit on public.docs;
create trigger docs_row_limit before insert on public.docs for each row execute function public.docs_row_limit();

-- ============================================================
-- 학교·학년별 교과서 출판사 공유 (같은 학교 같은 학년끼리)
-- 계정마다 "지금 학년" 한 줄씩 등록. 다른 사람 행은 직접 못 보고,
-- 아래 함수로 "출판사 목록 + 몇 명이 등록했는지" 만 볼 수 있음 (누가 했는지는 안 보임)
-- ============================================================
create table if not exists public.school_textbooks (
  user_id    uuid        not null default auth.uid() references auth.users (id) on delete cascade,
  grade      text        not null check (grade in ('중1', '중2', '중3', '고1', '고2', '고3')),
  school     text        not null check (char_length(school) between 1 and 40 and school !~ '\s'),   -- 띄어쓰기 없앤 학교 이름
  textbooks  jsonb       not null check (jsonb_typeof(textbooks) = 'array' and jsonb_array_length(textbooks) <= 40 and length(textbooks::text) <= 4000),
  updated_at timestamptz not null default now(),
  primary key (user_id, grade)
);
alter table public.school_textbooks enable row level security;
-- 🔒 다른 사람에게 보이는 값이라 모양을 엄격하게: [{subject, publisher}] 문자열만, 각 60자까지, <> 금지
alter table public.school_textbooks drop constraint if exists school_textbooks_shape;
alter table public.school_textbooks add constraint school_textbooks_shape check (
  not jsonb_path_exists(textbooks, '$[*] ? (@.type() != "object")')
  and not jsonb_path_exists(textbooks, '$[*].* ? (@.type() != "string")')
  and not jsonb_path_exists(textbooks, '$[*].* ? (@ like_regex "^.{61,}" flag "s" || @ like_regex "[<>]")')
  and not jsonb_path_exists(textbooks, '$[*].keyvalue() ? (@.key != "subject" && @.key != "publisher")')
) not valid;

drop policy if exists "school_textbooks: 내 것만 읽기" on public.school_textbooks;
drop policy if exists "school_textbooks: 내 것만 추가" on public.school_textbooks;
drop policy if exists "school_textbooks: 내 것만 수정" on public.school_textbooks;
drop policy if exists "school_textbooks: 내 것만 삭제" on public.school_textbooks;
create policy "school_textbooks: 내 것만 읽기" on public.school_textbooks for select to authenticated using (auth.uid() = user_id);
create policy "school_textbooks: 내 것만 추가" on public.school_textbooks for insert to authenticated with check (auth.uid() = user_id);
create policy "school_textbooks: 내 것만 수정" on public.school_textbooks for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "school_textbooks: 내 것만 삭제" on public.school_textbooks for delete to authenticated using (auth.uid() = user_id);
revoke all on public.school_textbooks from anon;
grant select, insert, update, delete on public.school_textbooks to authenticated;

-- 같은 학교·학년에서 다른 사람들이 등록한 출판사 묶음 (많이 등록한 순)
create or replace function public.school_textbook_choices(p_school text, p_grade text)
returns table (textbooks jsonb, people int)
language sql stable security definer set search_path = '' as $$
  select t.textbooks, count(*)::int
  from public.school_textbooks t
  where auth.uid() is not null
    and t.school = regexp_replace(coalesce(p_school, ''), '\s', '', 'g')
    and t.grade = p_grade
    and t.user_id <> auth.uid()
  group by t.textbooks
  order by count(*) desc, max(t.updated_at) desc
  limit 5;
$$;

-- 학교 이름 자동완성 (이름 + 등록한 사람 수만)
create or replace function public.school_names(p_q text)
returns table (school text, people int)
language sql stable security definer set search_path = '' as $$
  select t.school, count(distinct t.user_id)::int
  from public.school_textbooks t
  where auth.uid() is not null
    and char_length(regexp_replace(coalesce(p_q, ''), '\s', '', 'g')) >= 2
    and strpos(t.school, regexp_replace(p_q, '\s', '', 'g')) > 0
  group by t.school
  order by 2 desc, 1
  limit 10;
$$;
revoke all on function public.school_textbook_choices(text, text) from public, anon;
revoke all on function public.school_names(text) from public, anon;
grant execute on function public.school_textbook_choices(text, text) to authenticated;
grant execute on function public.school_names(text) to authenticated;
