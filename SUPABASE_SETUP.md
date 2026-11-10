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

## 💬 커뮤니티 (한 번만)
☰ 메뉴 → 💬 커뮤니티 게시판을 쓰려면 Supabase 에 게시판 표가 있어야 해요.
Supabase **SQL Editor → New query** 에 [`supabase/schema.sql`](supabase/schema.sql) 전체를 다시 붙여넣고 **Run** 하세요. (여러 번 실행해도 괜찮아요)

- 글·댓글 표는 앱에서 **직접 읽을 수 없고**, `community_*` 함수로만 읽고 써요.
- 🔒 비밀번호를 건 글은 목록에 **제목·별명만** 보여요. 내용·댓글은 비밀번호가 맞을 때만 함수가 돌려줘요 (글쓴이 본인은 비밀번호 없이 봐요).
- 비밀번호는 `pgcrypto` 의 bcrypt 해시로만 저장돼요. 한 계정이 한 글에 10분 동안 5번 넘게 틀리면 잠시 막혀요.
- 한 계정당 글은 하루 30개, 댓글은 하루 200개까지예요.

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
