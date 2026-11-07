-- 📋 '오늘 해야 할 일' 알림을 Supabase 가 정해진 시각에 바로 보내요
-- Supabase 대시보드 → SQL Editor → New query 에 이 내용을 그대로 붙여넣고 Run (여러 번 실행해도 괜찮아요)
--
-- 예전: GitHub Actions 가 전날 밤(실제로는 몇 시간씩 늦게) 다음 날 알림을 미리 예약 → 그 뒤에 적은 할 일은 알림에 안 들어감
-- 지금: 1분마다 확인해서 07:30·08:00·21:00 (schedule.json 의 todo_reminders) 가 되면 그 순간의 할 일 목록으로 보내요
-- 이걸 실행하면 GitHub Actions(run_supabase.py)는 할 일 알림을 따로 예약하지 않아요 (나머지 알람은 그대로)
--
-- 끄기: select cron.unschedule('alam-todo-reminders');

create extension if not exists pg_cron;
create extension if not exists pg_net;

-- 이미 보낸 알림 (같은 알림 두 번 안 보내게)
create table if not exists public.todo_sent (
  user_id uuid not null references auth.users (id) on delete cascade,
  day     date not null,
  slot    text not null,          -- 'HH:MM'
  sent_at timestamptz not null default now(),
  primary key (user_id, day, slot)
);
alter table public.todo_sent enable row level security;   -- 정책 없음 = 앱(로그인한 사람)은 못 봄
revoke all on public.todo_sent from anon, authenticated;

-- 표(주간·월간) 내용에서 그 날짜 줄의 [일정 칸, 할 일 칸]. 없으면 null
create or replace function public.alam_table_row(p_text text, p_day date)
returns text[] language plpgsql immutable set search_path = '' as $$
declare
  line text; cells text[]; m text[];
begin
  if p_text is null then return null; end if;
  foreach line in array string_to_array(p_text, E'\n') loop
    line := btrim(line);
    continue when left(line, 1) <> '|';
    cells := string_to_array(btrim(line, '|'), '|');
    continue when coalesce(array_length(cells, 1), 0) < 2;
    m := regexp_match(btrim(cells[1]), '^(\d{1,2})\s*/\s*(\d{1,2})');
    continue when m is null;
    if m[1]::int = extract(month from p_day)::int and m[2]::int = extract(day from p_day)::int then
      return array[btrim(cells[2]), btrim(coalesce(cells[3], ''))];
    end if;
  end loop;
  return null;
end $$;

-- 쉼표로 나누기 ([60,10] 같은 대괄호 안 쉼표는 무시)
create or replace function public.alam_split(p_cell text)
returns setof text language sql immutable set search_path = '' as $$
  select btrim(x) from regexp_split_to_table(coalesce(p_cell, ''), ',(?![^\[]*\])') as x where btrim(x) <> '';
$$;

-- 그날 일정·할 일 (alarm.py 의 Planner.day 와 같은 순서: 주간 표 → 월간 표 → 기본 시간표)
-- 돌려주는 값: {"events": [{"title","start","end"}], "memos": [...]}
create or replace function public.alam_day(p_user uuid, p_sched jsonb, p_day date)
returns jsonb language plpgsql stable set search_path = '' as $$
declare
  ws date := p_day - extract(dow from p_day)::int;          -- 그 주 일요일
  iso text := to_char(p_day, 'YYYY-MM-DD');
  wd text := (extract(isodow from p_day)::int - 1)::text;  -- 0=월 … 6=일
  v_row text[]; item text; m text[];
  events jsonb := '[]'; memos jsonb := '[]';
  sc jsonb := coalesce(p_sched -> 'school', '{}');
  off text; exam text; note text; drop_titles jsonb;
begin
  select public.alam_table_row(d.content, p_day) into v_row from public.docs d
    where d.user_id = p_user and d.path = 'plans/week/' || to_char(ws, 'YYYY-MM-DD') || '.md';
  if v_row is null then
    select public.alam_table_row(d.content, p_day) into v_row from public.docs d
      where d.user_id = p_user and d.path = 'plans/month/' || to_char(p_day, 'YYYY-MM') || '.md';
  end if;

  if v_row is not null then
    for item in select * from public.alam_split(v_row[1]) loop
      m := regexp_match(regexp_replace(item, '\s*\[[\d,\s]*\]$', ''),
                        '^(\d{1,2}):(\d{2})(\s*[~-]\s*(\d{1,2}):(\d{2}))?\s+(.+)$');
      if m is null then
        memos := memos || to_jsonb(item);   -- 시간이 없으면 할 일로
      else
        events := events || jsonb_build_object('title', btrim(m[6]),
          'start', lpad(m[1], 2, '0') || ':' || m[2],
          'end', case when m[4] is null then '' else lpad(m[4], 2, '0') || ':' || m[5] end);
      end if;
    end loop;
    select memos || coalesce(jsonb_agg(x), '[]') into memos from public.alam_split(v_row[2]) x;
  else
    events := coalesce(p_sched -> 'weekly' -> wd, '[]');
    off := sc -> 'off_days' ->> iso;
    if off is null then
      select v ->> 'name' into off from jsonb_array_elements(coalesce(sc -> 'vacations', '[]')) v
        where v ->> 'from' <= iso and iso <= v ->> 'to' limit 1;
    end if;
    if off is not null then
      drop_titles := coalesce(sc -> 'school_events', '[]');
      memos := memos || to_jsonb('🏫 ' || off || ' - 학교 안 감');
    else
      exam := sc -> 'exam_days' ->> iso;
      if exam is not null then
        select coalesce(jsonb_agg(t), '[]') into drop_titles from jsonb_array_elements_text(coalesce(sc -> 'school_events', '[]')) t
          where not coalesce(sc -> 'exam_keep_events', '["등교"]') ? t;
        memos := memos || to_jsonb('✏️ ' || exam || ' - 등교만 (하교·야자 없음)');
      end if;
    end if;
    if drop_titles is not null then
      select coalesce(jsonb_agg(e), '[]') into events from jsonb_array_elements(events) e
        where not drop_titles ? (e ->> 'title');
    end if;
    note := sc -> 'notes' ->> iso;
    if note is not null then memos := memos || to_jsonb(replace(replace(note, ',', '·'), '|', ' ')); end if;
    select coalesce(jsonb_agg(jsonb_build_object('title', e ->> 'title', 'start', e ->> 'start', 'end', coalesce(e ->> 'end', ''))), '[]')
      into events from jsonb_array_elements(events) e;
  end if;
  select coalesce(jsonb_agg(e order by e ->> 'start'), '[]') into events from jsonb_array_elements(events) e;
  return jsonb_build_object('events', events, 'memos', memos);
end $$;

-- 1분마다 실행: 알림 시각이 된 계정에 '오늘 해야 할 일' 보내기 (alarm.py 의 todo_reminders 와 같은 내용)
create or replace function public.send_todo_reminders()
returns int language plpgsql security definer set search_path = '' as $$
declare
  r record; sched jsonb; cfg jsonb; topic text;
  local_now timestamp; today date; now_hm text; wd text;
  v_slot text; v_day jsonb; todos text[]; commute jsonb; lines text[]; later text[];
  commute_at text; remaining_from text; title text; body text; left_min int;
  sent int := 0;
begin
  delete from public.todo_sent t where t.day < current_date - 7;
  for r in
    select s.user_id, s.content as settings, d.content as schedule
    from public.docs s join public.docs d on d.user_id = s.user_id and d.path = 'schedule.json'
    where s.path = 'settings.json'
  loop
    begin
      topic := btrim(coalesce(r.settings::jsonb ->> 'ntfy_topic', ''));
      continue when topic !~ '^[A-Za-z0-9_-]{1,64}$';
      sched := r.schedule::jsonb;
      cfg := sched -> 'todo_reminders';
      continue when cfg is null or jsonb_typeof(cfg) <> 'object';
      local_now := (coalesce(nullif(current_setting('alam.now', true), '')::timestamptz, now()) at time zone 'UTC')   -- alam.now: 시험용 시각
                    + make_interval(hours => coalesce((sched ->> 'timezone_offset_hours')::int, 9));
      today := local_now::date;
      now_hm := to_char(local_now, 'HH24:MI');
      wd := (extract(isodow from today)::int - 1)::text;
      commute_at := cfg ->> 'commute_at';
      remaining_from := coalesce(cfg ->> 'remaining_from', '00:00');
      v_day := null;
      for v_slot in
        select distinct t from (
          select jsonb_array_elements_text(coalesce(cfg -> 'daily', '[]')) t
          union all
          select jsonb_array_elements_text(coalesce(cfg -> 'weekday' -> wd, '[]'))
        ) x where t ~ '^\d{2}:\d{2}$' order by 1
      loop
        -- 시각이 됐고 20분이 안 지났고 아직 안 보냈으면
        continue when now_hm < v_slot
          or local_now >= today + v_slot::time + interval '20 minutes';
        continue when exists (select 1 from public.todo_sent x where x.user_id = r.user_id and x.day = today and x.slot = v_slot);
        if v_day is null then v_day := public.alam_day(r.user_id, sched, today); end if;
        select coalesce(array_agg(m), '{}') into todos from jsonb_array_elements_text(v_day -> 'memos') m
          where m !~ '^(✅|🏫|✏️)';
        select e into commute from jsonb_array_elements(v_day -> 'events') e where e ->> 'title' = '등교' limit 1;
        lines := '{}';
        if v_slot = commute_at and commute is not null then
          left_min := (split_part(commute ->> 'start', ':', 1)::int * 60 + split_part(commute ->> 'start', ':', 2)::int)
                    - (split_part(v_slot, ':', 1)::int * 60 + split_part(v_slot, ':', 2)::int);
          lines := lines || ('🏫 ' || (commute ->> 'start') || ' 등교' || case when left_min > 0 then ' (' || left_min || '분 남음)' else '' end) || ''::text;
        end if;
        lines := lines || '☑️ 할 일'::text;
        if cardinality(todos) = 0 then
          lines := lines || '· 아직 없어요. 앱에서 오늘 할 일을 적어 보세요!'::text;
        else
          lines := lines || array(select '· ' || t from unnest(todos) t);
        end if;
        if v_slot >= remaining_from then
          select coalesce(array_agg('· ' || (e ->> 'start') || case when e ->> 'end' <> '' then '~' || (e ->> 'end') else '' end || ' ' || (e ->> 'title')), '{}')
            into later from jsonb_array_elements(v_day -> 'events') e
            where e ->> 'start' >= v_slot or (e ->> 'end' <> '' and (e ->> 'end' <= e ->> 'start' or e ->> 'end' > v_slot));
          lines := lines || ''::text || '⏰ 남은 일정'::text;
          lines := lines || case when cardinality(later) = 0 then array['· 오늘 남은 일정 없음'] else later end;
        end if;
        body := array_to_string(lines, E'\n');
        if octet_length(body) > 3500 then body := left(body, 1100) || E'\n… (알림을 누르면 전체 표가 열려요)'; end if;
        title := '📋 오늘 해야 할 일 (' || cardinality(todos) || '개)' || case when v_slot = commute_at and commute is not null then ' · 등교' else '' end;
        perform net.http_post(
          url := 'https://ntfy.sh',
          body := jsonb_build_object('topic', topic, 'title', title, 'message', body, 'tags', jsonb_build_array('clipboard'),
                                     'priority', 3, 'click', 'https://mal-ba.github.io/alam/?day=' || to_char(today, 'YYYY-MM-DD')),
          headers := '{"Content-Type": "application/json"}'::jsonb);
        insert into public.todo_sent (user_id, day, slot) values (r.user_id, today, v_slot) on conflict do nothing;
        sent := sent + 1;
      end loop;
    exception when others then
      -- 한 계정의 시간표가 잘못돼도 다른 계정은 계속 (내용은 로그에 안 남겨요)
      raise warning 'todo reminder skipped for one account (%)', sqlstate;
    end;
  end loop;
  return sent;
end $$;
revoke all on function public.send_todo_reminders() from public, anon, authenticated;
revoke all on function public.alam_day(uuid, jsonb, date) from public, anon, authenticated;

-- GitHub Actions(run_supabase.py)가 "할 일 알림은 Supabase 가 보내요?" 확인하는 용도
create or replace function public.todo_reminders_on()
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (select 1 from cron.job where jobname = 'alam-todo-reminders' and active);
$$;
revoke all on function public.todo_reminders_on() from public, anon, authenticated;
grant execute on function public.todo_reminders_on() to service_role;

-- 1분마다 실행 + 실행 기록은 3일만 남기기
select cron.schedule('alam-todo-reminders', '* * * * *', 'select public.send_todo_reminders()');
select cron.schedule('alam-cron-cleanup', '17 4 * * *', $$delete from cron.job_run_details where end_time < now() - interval '3 days'$$);
