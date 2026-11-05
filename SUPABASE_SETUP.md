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

## 학교·학년별 교과서 출판사 공유 (한 번만)
같은 학교 같은 학년 친구가 등록한 출판사를 새로 로그인한 사람에게 "이거 맞아요?" 하고 보여 주려면 공유 표가 필요해요.
Supabase **SQL Editor → New query** 에 [`supabase/schema.sql`](supabase/schema.sql) 전체를 다시 붙여넣고 **Run** 하세요. (여러 번 실행해도 괜찮아요)

- 다른 사람에게는 **학교 이름, 학년, 출판사 목록, 몇 명이 등록했는지**만 보여요. 누가 등록했는지(계정·이메일)는 안 보여요.
- 공유되는 건 각자 **지금 학년(★)** 출판사뿐이에요.
