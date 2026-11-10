-- 📷 사진으로 채우기: 계정마다 하루 사용 횟수 기록 (Edge Function ai-scan 이 씀)
-- Supabase 대시보드 → SQL Editor 에 붙여 넣고 Run (한 번만)
create table if not exists public.ai_scans (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null,
  created_at timestamptz not null default now()
);
create index if not exists ai_scans_user_time on public.ai_scans (user_id, created_at desc);

-- 🔒 앱(브라우저)에서는 읽기·쓰기 못 하게: 정책 없이 RLS 만 켬 → 서버(service role)만 사용
alter table public.ai_scans enable row level security;
revoke all on public.ai_scans from anon, authenticated;

-- 오래된 기록은 지워도 돼요 (선택): delete from public.ai_scans where created_at < now() - interval '7 days';
