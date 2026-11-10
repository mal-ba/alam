# Supabase + 구글 로그인 설정 (한 번만)

계획·보고서·시험 데이터를 공개 GitHub 저장소에서 **Supabase**로 옮겨요.
옮기고 나면 **로그인한 구글 계정에서만** 자기 데이터가 보여요. 앱 코드는 공개라도 데이터는 비공개예요.

## 1. Supabase 프로젝트 만들기
1. https://supabase.com → **Start your project** → 구글 계정으로 가입
2. **New project** → 이름 `alam`, Region **Northeast Asia (Seoul)**, DB 비밀번호는 아무거나(따로 적어 두기) → Create
3. 왼쪽 **SQL Editor** → **New query** → 이 저장소의 [`supabase/schema.sql`](supabase/schema.sql) 내용을 붙여넣고 **Run**

## 2. 구글 로그인 켜기
1. Supabase 왼쪽 **Authentication → Sign In / Providers → Google** 을 열고, 화면에 나오는
   **Callback URL** (`https://<내프로젝트>.supabase.co/auth/v1/callback`)을 복사해 둬요
2. https://console.cloud.google.com → 새 프로젝트 만들기
3. **APIs & Services → OAuth consent screen**: External, 앱 이름(예: 내 계획표), 내 이메일 → 저장
   - **Test users**에 로그인할 구글 계정을 추가하거나, **Publish app**을 눌러 누구나 로그인할 수 있게 해요
4. **Credentials → Create credentials → OAuth client ID → Web application**
   - Authorized JavaScript origins: `https://mal-ba.github.io`
   - Authorized redirect URIs: 1번에서 복사한 **Callback URL**
   - 만들어지면 **Client ID**, **Client secret** 복사
5. Supabase **Google** 화면에 Client ID / Client secret 붙여넣고 **Enable** → Save
6. Supabase **Authentication → URL Configuration**
   - Site URL: `https://mal-ba.github.io/alam/`
   - Redirect URLs에 `https://mal-ba.github.io/alam/` 추가

## 3. 키 연결
Supabase **Project Settings → API (API Keys)** 에서:

| 값 | 어디에 | 공개돼도? |
|---|---|---|
| **Project URL** | Claude에게 알려주기 + GitHub Secret `SUPABASE_URL` | 괜찮아요 |
| **anon public** (또는 **publishable**) 키 | Claude에게 알려주기 → `docs/config.js` | 괜찮아요 (로그인 + 행 보안으로 보호) |
| **service_role** (또는 **secret**) 키 | **GitHub Secret `SUPABASE_SERVICE_KEY` 에만!** | ❌ 절대 채팅·코드에 붙여넣지 마세요 |

GitHub Secrets: 저장소 **Settings → Secrets and variables → Actions → New repository secret**

## 4. 옮기기
1. 앱을 열고 **구글로 로그인**
2. **📦 예전 GitHub 저장소 데이터 가져오기** → 내 계획·보고서·시험이 이 계정으로 들어가요
3. **⚙️ → 🔔 ntfy 알림 토픽**에 지금 쓰는 토픽 이름 입력 → 저장
4. 확인되면 Claude에게 말하기 → 공개 저장소에서 개인 데이터(`plans/`, 시간표)를 지워요

## 알림은 어떻게 오나요
매일 22:00·00:00 GitHub Actions가 `run_supabase.py`를 실행해요.
`settings.json`에 ntfy 토픽이 있는 **계정마다** 그 계정의 일정으로만 알람을 예약해요.
공개 로그에는 이메일이나 일정 내용 없이 "계정 1: 알림 8개 예약"처럼 개수만 남아요.

### 📋 '오늘 해야 할 일' 알림을 정시에 보내기 (한 번만)
GitHub Actions 예약 실행은 몇 시간씩 늦게 돌 때가 많아요. 그래서 할 일 알림이 **예약할 때의 할 일**로만 만들어져서,
그 뒤에 적은 할 일은 알림에 안 들어갔어요. 이걸 Supabase 가 직접 정시에 보내게 바꿀 수 있어요.

1. Supabase **SQL Editor → New query** 에 [`supabase/todo_reminders.sql`](supabase/todo_reminders.sql) 내용을 붙여넣고 **Run**
   (pg_cron·pg_net 확장을 켜요. "extension ... must be enabled" 같은 오류가 나면 **Database → Extensions** 에서 `pg_cron`, `pg_net` 을 켜고 다시 Run)
2. 끝! 1분마다 확인해서 `schedule.json` 의 `todo_reminders` 시각(07:30·08:00·21:00 등)이 되면 **그 순간의 할 일 목록**으로 보내요.
   GitHub Actions 는 이걸 알아채고 할 일 알림만 따로 예약하지 않아요 (나머지 일정 알람·요약은 그대로).

- 알림 시각에서 20분 안에 못 보내면 그 알림은 건너뛰어요. 같은 알림은 한 번만 가요.
- 끄려면 SQL Editor 에서 `select cron.unschedule('alam-todo-reminders');` → 다음 실행부터 GitHub Actions 가 다시 예약해요.

## 학교·학년별 교과서 출판사 공유 (한 번만)
같은 학교 같은 학년 친구가 등록한 출판사를 새로 로그인한 사람에게 "이거 맞아요?" 하고 보여 주려면 공유 표가 필요해요.
Supabase **SQL Editor → New query** 에 [`supabase/schema.sql`](supabase/schema.sql) 전체를 다시 붙여넣고 **Run** 하세요. (여러 번 실행해도 괜찮아요)

- 다른 사람에게는 **학교 이름, 학년, 출판사 목록, 몇 명이 등록했는지**만 보여요. 누가 등록했는지(계정·이메일)는 안 보여요.
- 공유되는 건 각자 **지금 학년(★)** 출판사뿐이에요.

## 💬 커뮤니티 (설정 필요 없음)
☰ 메뉴 → 💬 커뮤니티는 따로 할 일이 없어요. 위 3번의 GitHub Secrets(`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`)만 있으면 돼요.

- 게시물은 쓴 사람의 Supabase 칸(`community/posts/…json`)에 저장돼요.
- GitHub Actions **커뮤니티 피드**(`.github/workflows/community.yml`)가 5분마다 모두의 게시물을 모아 Supabase **Storage** 공개 버킷 `community` 에 올려요. 버킷은 처음 실행할 때 알아서 만들어요.
- 바로 보고 싶으면 저장소 **Actions → 커뮤니티 피드 → Run workflow**.

## 전국 학교 목록 (한 번만: 공공데이터 키 넣기)
이름이 같은 학교가 많아서, 앱에서 **전국 중·고등학교 목록**을 주소(지번·도로명)와 함께 보여 주고 고르게 해요.
목록은 GitHub Actions(`.github/workflows/schools.yml`)가 한 달에 한 번 공공데이터에서 받아 `docs/schools.json` 으로 저장해요.

1. https://www.data.go.kr 회원가입 → 로그인
2. 검색창에 **전국초중등학교위치표준데이터** → **오픈API** 탭 → **활용신청** (목적: 개인 공부용 앱의 학교 선택 등). 보통 바로 승인돼요
3. **마이페이지 → 데이터활용 → Open API → 활용신청 현황** → 그 API → **일반 인증키 (Decoding)** 복사
4. GitHub 저장소 **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `DATA_GO_KR_KEY`, Secret: 복사한 키
5. 저장소 **Actions → 전국 학교 목록 모으기 → Run workflow** → 1~2분 뒤 `docs/schools.json` 이 생기면 끝

**키 없이 하는 방법 (CSV 파일):** data.go.kr 의 전국초중등학교위치표준데이터 페이지에서 **CSV 파일을 내려받아** Claude 에게 주면
`python schools.py 파일.csv` 로 `docs/schools.json` 을 만들어 올려요. 지금 목록은 이렇게 만든 거예요 (기준일 2026-10-01).
데이터가 바뀌면(보통 1년에 몇 번) 새 CSV 로 다시 하면 돼요. 키가 없으면 매달 Actions 는 아무것도 바꾸지 않고 넘어가요.

- 대신 나이스(https://open.neis.go.kr) 인증키를 `NEIS_KEY` 로 넣어도 돼요. 이 경우 도로명주소만 있고 **지번주소·지도 위치는 없어요**.
- 목록이 없을 때는 앱이 예전처럼 학교 이름을 직접 적게 해요.
- 학교 목록에서 고른 학교는 **학교 고유번호**로 친구들과 출판사를 맞춰요. 이름이 같아도 다른 학교와 섞이지 않아요.

## 📷 사진으로 채우기
시험 범위표 · 수업 필기(보고서) · 계획표를 **사진으로 찍으면** AI(Claude)가 읽어서 앱 형식에 맞게 채워 줘요.
채운 뒤에는 **고쳐서 저장**하거나 **💾 그대로 저장**하면 돼요.

| 어디서 | 버튼 | 무엇이 채워지나 |
|---|---|---|
| 보고서 → 📅 날짜별 | 날짜 옆 📷 / 수정 칸의 📷 | 과목별 수업 내용, 중요한 것, 외울 것, 기억할 것(숙제·수행 날짜), 기타 |
| 보고서 → 📝 자유 | 📷 사진으로 쓰기 | 제목, 과목, 내용, 중요한 것 등 |
| 시험 | 📷 시험 범위표·수행평가 안내 사진으로 추가 | 시험 이름·기간, 과목별 시험날·범위(진도 0%에서 시작), 메모 |
| 주간 / 월간 | 📷 계획표 사진으로 채우기 | 날짜별 일정(시간)·할 일, 주간 GRIT·MUST DO / 월간 목표·MEMO — 확인 칸에서 **➕ 원래 계획에 더하기** 또는 **🔁 사진 내용으로 바꾸기** |

사진은 한 번에 4장까지, 앱이 크기를 줄여서 보내요. 사진은 **저장하지 않고** 읽기만 해요.

**설정 없이도 돼요 (기기에서 읽기, 무료):** AI 서버를 설정하지 않으면 앱이 **휴대폰 안에서 직접** 글자를 읽어요
(Tesseract.js 글자 인식 + 규칙으로 과목·날짜·시간·범위를 나눔). 처음 한 번 글자 데이터(약 5MB)를 받고, 그다음부턴 기기에 저장돼 빨라요.
읽기 전에 사진을 다듬어요: 그림자·누런 종이색을 없애고 글씨를 진하게 한 뒤, 글자 크기에 맞춰 크기를 바꿔 4번 읽고 줄마다 가장 자신 있는 결과를 골라요.
흐리게 읽힌 과목 이름("소하" → 수학, "였어" → 영어)은 자음·모음 단위로 비교해 바로잡아요.
인쇄된 글씨(시험 범위 공지, 프린트)는 잘 읽고, **손글씨도 또박또박 쓴 건 꽤 읽지만** 글자 몇 개는 틀릴 수 있어요. 흘려 쓴 손글씨까지 정확히 읽게 하려면 아래 AI 설정을 해 주세요.
잘 읽히게 찍는 법: 밝은 곳에서, 종이가 화면에 꽉 차게, 위에서 똑바로, 흔들리지 않게.
AI 서버가 설정돼 있으면 AI로 먼저 읽고, 실패하면 기기에서 읽기로 넘어가요.

### (선택) AI 로 더 정확하게: 설정
1. **Claude API 키 만들기**: https://platform.claude.com → API Keys → Create Key (결제 수단 등록 필요. 사진 한 장에 보통 몇십 원 정도)
2. **키 넣기**: Supabase 대시보드 → **Edge Functions → Secrets** → Add new secret
   - Name: `ANTHROPIC_API_KEY`, Value: 만든 키 (🔒 키는 서버에만 있고 앱·저장소에는 절대 안 들어가요)
3. **서버 함수 만들기** (둘 중 하나)
   - **대시보드에서**: Edge Functions → **Deploy a new function → Via Editor** → 이름 `ai-scan` → [`supabase/functions/ai-scan/index.ts`](supabase/functions/ai-scan/index.ts) 내용을 통째로 붙여넣고 **Deploy**
   - **CLI 로**: `supabase functions deploy ai-scan --project-ref <프로젝트 ID>`
   - 함수 안에서 로그인 토큰을 직접 확인해요. 새 API 키(`sb_publishable_…`)를 쓰는 프로젝트에서 401 이 나면 함수 설정의 **Verify JWT** 를 꺼 주세요 (CLI: `--no-verify-jwt`).
4. **(권장) 하루 사용 횟수 제한**: SQL Editor 에 [`supabase/ai_scan.sql`](supabase/ai_scan.sql) 을 붙여넣고 **Run** → 계정마다 하루 40번까지 (`DAILY_LIMIT` 로 바꿀 수 있어요). 이 표가 없으면 제한 없이 동작해요.

- 🔒 로그인한 사람만 쓸 수 있어요. 앱은 `https://<프로젝트>.supabase.co/functions/v1/ai-scan` 로만 보내서 보안 정책(CSP)을 바꿀 필요가 없어요.
- 모델은 `claude-opus-5-5` (함수 맨 위 `MODEL`). 손글씨가 많이 흐리면 더 밝게, 가깝게 찍어 주세요.
