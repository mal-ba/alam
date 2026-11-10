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

-- ============================================================
-- 💬 커뮤니티 (모두가 같이 보는 게시판)
-- 로그인한 사람은 누구나 글을 쓸 수 있고, 글마다 🔒 비밀번호를 걸 수 있어요.
-- 비밀번호를 건 글은 제목·글쓴이(별명)만 목록에 보이고, 내용·댓글은 비밀번호를 아는 사람만 봐요.
--   - 표를 직접 읽을 수 없게 막고(정책 없음 + 권한 회수), 아래 함수로만 읽고 써요.
--   - 비밀번호는 bcrypt 해시로만 저장 (DB 를 봐도 원래 비밀번호는 몰라요)
--   - 틀린 비밀번호는 한 사람이 한 글에 10분 동안 5번까지만 (마구 넣어 보기 막기)
--   - 누가 썼는지(계정·이메일)는 안 보이고, 글 쓸 때 적은 별명만 보여요
-- ============================================================
create extension if not exists pgcrypto with schema extensions;

create table if not exists public.community_posts (
  id         bigint      generated always as identity primary key,
  author_id  uuid        not null default auth.uid() references auth.users (id) on delete cascade,
  nickname   text        not null check (char_length(nickname) between 1 and 20),
  title      text        not null check (char_length(title) between 1 and 100),
  body       text        not null check (char_length(body) between 1 and 20000),
  pw_hash    text,                                   -- null 이면 누구나 보는 글
  created_at timestamptz not null default now(),
  updated_at timestamptz
);
create index if not exists community_posts_author on public.community_posts (author_id, created_at);

create table if not exists public.community_comments (
  id         bigint      generated always as identity primary key,
  post_id    bigint      not null references public.community_posts (id) on delete cascade,
  author_id  uuid        not null default auth.uid() references auth.users (id) on delete cascade,
  nickname   text        not null check (char_length(nickname) between 1 and 20),
  body       text        not null check (char_length(body) between 1 and 1000),
  created_at timestamptz not null default now()
);
create index if not exists community_comments_post on public.community_comments (post_id, id);
create index if not exists community_comments_author on public.community_comments (author_id, created_at);

create table if not exists public.community_pw_fails (
  user_id uuid        not null references auth.users (id) on delete cascade,
  post_id bigint      not null references public.community_posts (id) on delete cascade,
  at      timestamptz not null default now()
);
create index if not exists community_pw_fails_k on public.community_pw_fails (user_id, post_id, at);

-- 🔒 표는 아무도 직접 못 읽고 못 써요 (함수로만)
alter table public.community_posts    enable row level security;
alter table public.community_comments enable row level security;
alter table public.community_pw_fails enable row level security;
revoke all on public.community_posts, public.community_comments, public.community_pw_fails from anon, authenticated;

-- (안에서만 쓰는 함수) 이 글을 볼 수 있나? 'ok' | 'need_pw' | 'wrong:<남은 횟수>' | 'locked' | 'none'
create or replace function public.community_access(p_id bigint, p_pw text) returns text
language plpgsql security definer set search_path = '' as $$
declare h text; a uuid; fails int;
begin
  select pw_hash, author_id into h, a from public.community_posts where id = p_id;
  if not found then return 'none'; end if;
  if h is null or a = auth.uid() then return 'ok'; end if;
  select count(*) into fails from public.community_pw_fails
   where user_id = auth.uid() and post_id = p_id and at > now() - interval '10 minutes';
  if fails >= 5 then return 'locked'; end if;
  if coalesce(p_pw, '') = '' then return 'need_pw'; end if;
  if extensions.crypt(p_pw, h) = h then
    delete from public.community_pw_fails where user_id = auth.uid() and post_id = p_id;
    return 'ok';
  end if;
  insert into public.community_pw_fails (user_id, post_id) values (auth.uid(), p_id);
  return 'wrong:' || (4 - fails);
end $$;
revoke all on function public.community_access(bigint, text) from public, anon, authenticated;

-- 글 목록 (최신순 30개씩, p_before 보다 오래된 것). 비밀글은 내용 미리보기 없이
create or replace function public.community_list(p_before bigint default null, p_q text default null)
returns table (id bigint, nickname text, title text, preview text, locked boolean, mine boolean, comments int, created_at timestamptz, updated_at timestamptz)
language sql stable security definer set search_path = '' as $$
  select p.id, p.nickname, p.title,
         case when p.pw_hash is null then left(p.body, 120) end,
         p.pw_hash is not null, p.author_id = auth.uid(),
         (select count(*)::int from public.community_comments c where c.post_id = p.id),
         p.created_at, p.updated_at
  from public.community_posts p
  where auth.uid() is not null
    and (p_before is null or p.id < p_before)
    and (coalesce(trim(p_q), '') = '' or strpos(lower(p.title), lower(trim(p_q))) > 0)
  order by p.id desc
  limit 30;
$$;

-- 글 열기: 비밀글이면 비밀번호가 맞아야 내용·댓글이 와요
create or replace function public.community_open(p_id bigint, p_pw text default null) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare st text; r jsonb;
begin
  if auth.uid() is null then return jsonb_build_object('error', 'login'); end if;
  st := public.community_access(p_id, p_pw);
  if st <> 'ok' then return jsonb_build_object('error', st); end if;
  select jsonb_build_object(
    'post', jsonb_build_object('id', p.id, 'nickname', p.nickname, 'title', p.title, 'body', p.body,
             'locked', p.pw_hash is not null, 'mine', p.author_id = auth.uid(), 'created_at', p.created_at, 'updated_at', p.updated_at),
    'comments', coalesce((select jsonb_agg(jsonb_build_object('id', c.id, 'nickname', c.nickname, 'body', c.body,
             'mine', c.author_id = auth.uid(), 'created_at', c.created_at) order by c.id)
             from public.community_comments c where c.post_id = p.id), '[]'::jsonb))
  into r from public.community_posts p where p.id = p_id;
  return r;
end $$;

-- 비밀번호 검사: 4~50자 (빈 값 = 비밀번호 없음)
create or replace function public.community_pw_hash(p_pw text) returns text
language plpgsql security definer set search_path = '' as $$
begin
  if coalesce(p_pw, '') = '' then return null; end if;
  if char_length(p_pw) not between 4 and 50 then
    raise exception '비밀번호는 4~50자로 정해 주세요' using errcode = '22023';
  end if;
  return extensions.crypt(p_pw, extensions.gen_salt('bf', 8));
end $$;
revoke all on function public.community_pw_hash(text) from public, anon, authenticated;

-- 글 쓰기 → 새 글 번호. 한 계정이 하루 30개까지
create or replace function public.community_write(p_title text, p_body text, p_nickname text, p_pw text default null) returns bigint
language plpgsql security definer set search_path = '' as $$
declare nid bigint;
begin
  if auth.uid() is null then raise exception '로그인이 필요해요' using errcode = '42501'; end if;
  if (select count(*) from public.community_posts where author_id = auth.uid() and created_at > now() - interval '1 day') >= 30 then
    raise exception '글은 하루에 30개까지 쓸 수 있어요' using errcode = '54000';
  end if;
  insert into public.community_posts (nickname, title, body, pw_hash)
  values (trim(p_nickname), trim(p_title), trim(p_body), public.community_pw_hash(p_pw))
  returning id into nid;
  return nid;
end $$;

-- 내 글 고치기. p_pw: null = 비밀번호 그대로, '' = 비밀번호 없애기, 그 밖 = 새 비밀번호
create or replace function public.community_edit(p_id bigint, p_title text, p_body text, p_nickname text, p_pw text default null) returns void
language plpgsql security definer set search_path = '' as $$
begin
  update public.community_posts
     set title = trim(p_title), body = trim(p_body), nickname = trim(p_nickname), updated_at = now(),
         pw_hash = case when p_pw is null then pw_hash else public.community_pw_hash(p_pw) end
   where id = p_id and author_id = auth.uid();
  if not found then raise exception '내가 쓴 글만 고칠 수 있어요' using errcode = '42501'; end if;
end $$;

-- 내 글 지우기 (댓글도 같이)
create or replace function public.community_delete(p_id bigint) returns void
language plpgsql security definer set search_path = '' as $$
begin
  delete from public.community_posts where id = p_id and author_id = auth.uid();
  if not found then raise exception '내가 쓴 글만 지울 수 있어요' using errcode = '42501'; end if;
end $$;

-- 댓글 달기: 비밀글이면 비밀번호가 맞아야 해요. 한 계정이 하루 200개까지
create or replace function public.community_comment(p_id bigint, p_pw text, p_body text, p_nickname text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare st text;
begin
  if auth.uid() is null then return jsonb_build_object('error', 'login'); end if;
  st := public.community_access(p_id, p_pw);
  if st <> 'ok' then return jsonb_build_object('error', st); end if;
  if (select count(*) from public.community_comments where author_id = auth.uid() and created_at > now() - interval '1 day') >= 200 then
    raise exception '댓글은 하루에 200개까지 달 수 있어요' using errcode = '54000';
  end if;
  insert into public.community_comments (post_id, nickname, body) values (p_id, trim(p_nickname), trim(p_body));
  return public.community_open(p_id, p_pw);
end $$;

-- 내 댓글 지우기 (글쓴이는 자기 글에 달린 댓글도 지울 수 있어요)
create or replace function public.community_comment_delete(p_comment_id bigint) returns void
language plpgsql security definer set search_path = '' as $$
begin
  delete from public.community_comments c
   where c.id = p_comment_id
     and (c.author_id = auth.uid() or exists (select 1 from public.community_posts p where p.id = c.post_id and p.author_id = auth.uid()));
  if not found then raise exception '내가 쓴 댓글만 지울 수 있어요' using errcode = '42501'; end if;
end $$;

revoke all on function public.community_list(bigint, text), public.community_open(bigint, text),
  public.community_write(text, text, text, text), public.community_edit(bigint, text, text, text, text),
  public.community_delete(bigint), public.community_comment(bigint, text, text, text),
  public.community_comment_delete(bigint) from public, anon;
grant execute on function public.community_list(bigint, text), public.community_open(bigint, text),
  public.community_write(text, text, text, text), public.community_edit(bigint, text, text, text, text),
  public.community_delete(bigint), public.community_comment(bigint, text, text, text),
  public.community_comment_delete(bigint) to authenticated;
