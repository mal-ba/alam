# 🔒 보안 정리

이 저장소는 **공개**예요. 코드·Actions 로그는 누구나 볼 수 있고, 개인 데이터는 Supabase 에만 있어요.
아래는 무엇을 어떻게 지키는지, 그리고 **코드로는 못 해서 대시보드에서 직접 해야 하는 일**이에요.

## ✅ 코드로 해 둔 것

### 개인 정보가 공개된 곳에 드러나지 않게
| 어디 | 무엇을 |
|---|---|
| Actions 로그 (`run_supabase.py`) | `alarm.py` 의 출력·경고(**stderr 포함**)를 전부 가두고, 오류도 종류만 찍어요. 이메일·일정 내용·토픽은 로그에 안 나와요 (예전엔 계획표의 이상한 날짜 칸 내용이 경고로 로그에 찍힐 수 있었어요) |
| 알람 워크플로 | 예전 "저장소 파일 방식"(계획표를 공개 저장소에 커밋)을 없앴어요. 이제 저장소에 아무것도 쓰지 않고 **읽기 권한만** 가져요 |
| ntfy 토픽 | ntfy.sh 토픽은 이름만 알면 누구나 구독해요. ⚙️ 에서 짧거나 쉬운 이름이면 경고하고, 🎲 로 추측하기 어려운 이름(80비트)을 만들어 줘요 |
| 로그아웃 | 기기에 남은 내 데이터(예전 GitHub 토큰, 장소, 코딩 진도)를 지우고 새로 시작해요 |
| 예전 GitHub 토큰 | Supabase 를 쓰면 기기에 남아 있던 `github_pat_…` 토큰을 자동으로 지워요 |
| `.gitignore` | `.env`, `schedule.json`, `plans/`, 키 파일, CSV 를 실수로 커밋하지 않게 |

### 웹 앱 (helmet 대신 — GitHub Pages 는 헤더를 못 붙여서 `<meta>` 로)
- **CSP (보안 정책)** `docs/index.html` 맨 위: 이 앱이 실행·연결할 수 있는 곳을 정해 뒀어요.
  누군가 글 속에 `<script>`·`onerror=` 를 끼워 넣어도 실행되지 않고, 로그인 정보를 모르는 사이트로 보낼 수도 없어요.
  - 이걸 위해 앱 코드를 `docs/app.js` 로 뺐어요 (인라인 스크립트 금지).
  - **새 외부 사이트(스크립트·API)를 쓰려면 CSP 에 주소를 더해야 해요.** 안 더하면 콘솔에 `Refused to …` 가 떠요.
  - `'unsafe-eval'` 은 코딩 공부의 자바스크립트 실행(웹 워커)과 파이썬(Pyodide) 때문에 남겨 뒀어요.
- **SRI**: jsDelivr 에서 받는 `supabase-js`·Leaflet 파일은 해시로 검사해요. CDN 파일이 바꿔치기되면 실행하지 않아요.
  버전을 올리면 `integrity` 값도 새로 넣어야 해요 (`npm pack 패키지@버전` → `openssl dgst -sha384 -binary 파일 | base64`).
- **클릭재킹 방지** (`docs/boot.js`): 다른 사이트의 틀(iframe) 안에서 열리면 화면을 숨겨요.
- **Referrer**: 다른 사이트로 갈 때 주소 전체를 넘기지 않아요. 바깥 링크는 `rel="noopener noreferrer"`.
- **XSS**: 화면에 넣는 값은 모두 `esc()` (이제 `'` 도), 바깥에서 온 링크(뉴스 RSS 등)는 `safeUrl()` 로 `http(s)` 만 — `javascript:` 링크는 막아요. `news.py` 도 모을 때 `http(s)` 가 아닌 링크는 버려요.
- **코딩 공부 HTML 실행 칸** (`docs/sandbox.html`): 주인 없는 출처(`null`)의 격리된 틀에서 실행돼서, 붙여 넣은 코드가 로그인 정보(localStorage)에 닿지 못해요. 이 파일을 직접 열면 아무것도 실행하지 않아요.

### Supabase (`supabase/schema.sql`)
- 모든 표에 **행 단위 보안(RLS)**: 내 행만 읽기·쓰기, 로그인 안 한 사람(anon)은 아무것도 못 해요.
- 구글 계정만 있으면 누구나 로그인할 수 있어서, 한 계정이 DB 를 채우지 못하게 **크기 제한**: 파일 하나 2MB, 계정당 3000개, 경로는 200자 · `..`·절대경로·제어문자 금지.
- 다른 사람에게 보이는 **학교 출판사 공유**는 `[{subject, publisher}]` 모양·60자·`<>` 금지로 DB 가 검사해요. 누가 등록했는지는 안 보여요.
- **💬 커뮤니티**: 게시물은 각자 자기 `docs` 칸에 저장되고, Actions(`community_feed.py`)가 비밀 키로 모아 Storage 공개 버킷 `community` 에 `feed.json`·사진으로 올려요. 피드는 주소를 알면 누구나 볼 수 있어요. 🔒 게시물은 브라우저에서 PBKDF2(60만 번)+AES-GCM 으로 암호화한 것만 올라가고, 원래 글·사진·열쇠는 피드에 안 넣어요 (열쇠는 글쓴이 자기 칸에만). 암호문이 공개라 짧은 비밀번호는 풀릴 수 있어서 6자 이상만 받아요. 피드에는 계정 번호 대신 sha256 해시 앞 16자리만, 로그에는 개수만.
- `security definer` 함수는 `search_path = ''` 로 고정해 다른 스키마의 함수로 바꿔치기되지 않게 했어요.
- 알림 실행(`run_supabase.py`)은 `SUPABASE_URL` 이 `https://<프로젝트>.supabase.co` 일 때만 비밀 키를 보내고, ntfy 토픽은 영문·숫자·`_-` 만 받아요.

### GitHub Actions
- 액션을 **커밋 SHA 로 고정** (태그가 바꿔치기돼도 안전). `.github/dependabot.yml` 이 한 달에 한 번 새 버전 PR 을 만들어 줘요.
- 알람 작업은 `contents: read` + `persist-credentials: false` (토큰을 디스크에 안 남김), 모든 작업에 시간 제한.
- 수동 실행 입력값(연도)은 따옴표로 감싸고 숫자만 받아요.

## 🙋 직접 해야 하는 일 (대시보드)

1. **Supabase SQL 다시 실행 (꼭!)** — Supabase → SQL Editor → New query → [`supabase/schema.sql`](supabase/schema.sql) 전체 붙여넣고 Run.
   여러 번 실행해도 괜찮고, 이미 있는 데이터는 그대로예요. 이걸 해야 크기 제한·공유 검사가 켜져요.
2. **ntfy 토픽 바꾸기** — 앱 ⚙️ → 🔔 옆 🎲 → 저장 → 휴대폰 ntfy 앱에서 **새 토픽 구독**(예전 토픽은 구독 취소).
3. **GitHub 저장소 Settings**
   - *Code security*: **Secret scanning** + **Push protection** 켜기 (비밀 키를 실수로 올리면 막아 줘요), **Dependabot alerts** 켜기
   - *Actions → General → Workflow permissions*: **Read repository contents** 로 (각 워크플로가 필요한 권한은 파일에 따로 적혀 있어요)
   - *Actions → General*: "Require approval for all outside collaborators" (포크 PR 이 Actions 를 마음대로 못 돌리게)
   - *Branches*: `main` 에 브랜치 보호 규칙 (강제 push·삭제 금지)
4. **GitHub 이메일 숨기기** — 커밋에 gmail 주소가 공개로 보여요. github.com → Settings → Emails → **Keep my email addresses private** + **Block command line pushes that expose my email**.
   이미 올라간 예전 커밋의 주소는 남아 있어요 (지우려면 기록을 다시 써야 해서 따로 정해요).
5. **Supabase Authentication**
   - *Sign In / Providers*: 구글만 쓰면 **Email** 로그인은 꺼 두기
   - *URL Configuration*: Redirect URLs 에 `https://mal-ba.github.io/alam/` 만 (와일드카드 `**` 없이)
   - 친구들만 쓰게 하려면 구글 OAuth 동의 화면을 **Testing** 으로 두고 Test users 에 계정 추가 (지금처럼 누구나 쓰게 하려면 Publish 그대로 — 데이터는 RLS 로 나뉘어 있어요)
   - **Advisors → Security Advisor** 에서 경고가 없는지 한 번 보기
6. **카카오 키를 넣는다면** — 카카오 디벨로퍼스 → 앱 → 플랫폼 → Web 에 `https://mal-ba.github.io` **만** 등록 (다른 사이트가 내 키를 못 쓰게).
7. **키를 채팅·코드에 붙여넣은 적이 있다면** — Supabase → Project Settings → API Keys 에서 **secret 키를 새로 만들고** GitHub Secret `SUPABASE_SERVICE_KEY` 를 바꾼 뒤, 예전 키는 지우기.

## 문제를 발견하면
공개 이슈 대신 저장소 주인에게 직접 알려 주세요.
