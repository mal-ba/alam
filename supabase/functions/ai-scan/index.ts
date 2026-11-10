// 📷 사진 → AI → 앱 형식(JSON)
// 시험 범위표·수업 필기(보고서)·계획표 사진을 받아서, 앱의 저장 형식에 맞는 JSON 으로 돌려줘요.
// 앱(docs/app.js)이 이 JSON 으로 입력 칸을 채우고, 사람이 고치거나 그대로 저장해요.
//
// 필요한 것 (Supabase 대시보드 → Edge Functions → Secrets):
//   ANTHROPIC_API_KEY   Claude API 키 (https://platform.claude.com)
// 자동으로 들어 있는 것: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
// 설치 방법은 SUPABASE_SETUP.md 의 "📷 사진으로 채우기" 참고.
import Anthropic from "npm:@anthropic-ai/sdk@1.7.0";
import { createClient } from "npm:@supabase/supabase-js@2.119.0";

const MODEL = "claude-opus-5-5";
const DAILY_LIMIT = 40;            // 계정마다 하루(24시간) 최대 몇 번
const MAX_IMAGES = 4;
const MAX_B64 = 5_000_000;         // 사진 한 장 base64 최대 길이 (앱에서 줄여서 보내요)
const MEDIA = new Set(["image/jpeg", "image/png", "image/webp", "image/gif"]);

const CORS = {
  "Access-Control-Allow-Origin": "*",   // 로그인 토큰(JWT)을 확인하니까 출처는 막지 않아요
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, "Content-Type": "application/json" } });

/* ---------- 종류별 JSON 형식 ---------- */
const str = { type: "string" };
const obj = (props: Record<string, unknown>) => ({
  type: "object", properties: props, required: Object.keys(props), additionalProperties: false,
});
const arr = (items: unknown) => ({ type: "array", items });

const SCHEMAS: Record<string, Record<string, unknown>> = {
  report: obj({
    classes: arr(obj({ subject: str, text: str })),
    important: str, memorize: str, remember: str, etc: str,
  }),
  note: obj({ title: str, subject: str, body: str, important: str, memorize: str, remember: str, etc: str }),
  exam: obj({
    kind: { type: "string", enum: ["정기", "수행"] },
    name: str, subject: str, date: str, end: str,
    subjects: arr(obj({ subject: str, date: str, ranges: arr(obj({ text: str })) })),
    ranges: arr(obj({ text: str })),
    memo: str,
  }),
  plan: obj({
    grit: arr(obj({ subject: str, content: str, day: str })),
    must: arr(str),
    goal: arr(str),
    memo: arr(str),
    days: arr(obj({
      date: str,
      events: arr(obj({ start: str, end: str, title: str })),
      tasks: arr(str),
    })),
  }),
};

const COMMON = `너는 한국 중·고등학생의 공부 계획 앱을 돕는 도우미야. 사진(손글씨·인쇄물·칠판·화면 캡처)을 읽고 앱의 저장 형식 JSON 으로 옮겨.
규칙:
- 사진에 실제로 있는 내용만 옮겨. 지어내지 마. 읽을 수 없는 칸은 빈 문자열("")이나 빈 배열로.
- 원래 글의 순서·구조(번호, 단원, 소제목)를 최대한 그대로 살려.
- 여러 줄 칸(text, body, important, memorize, remember, etc, memo)은 줄바꿈(\\n)으로 나눠. 목록 칸은 한 줄에 하나씩, 앞에 "-" 나 "•" 는 붙이지 마.
- 과목 이름은 학생이 쓰는 이름 그대로 (예: 수학, 공통수학1, 통합과학, 영어).
- 날짜는 YYYY-MM-DD. 연도가 없으면 오늘 날짜(아래)를 기준으로 가장 가까운 앞날로 정해. 날짜를 모르면 "".
- 시간은 24시간제 HH:MM (예: 오후 7시 → 19:00). 모르면 "".
- 쉼표(,)와 세로줄(|)은 앱에서 구분 기호라서, 내용 안에서는 쓰지 말고 "·" 로 바꿔.`;

function prompt(kind: string, ctx: Record<string, unknown>): string {
  const c = (k: string) => String(ctx[k] ?? "").slice(0, 400);
  const head = `${COMMON}\n오늘 날짜: ${c("today")}\n`;
  const subj = Array.isArray(ctx.subjects) && ctx.subjects.length
    ? `이 학생의 과목들(참고용): ${(ctx.subjects as unknown[]).slice(0, 40).map(String).join(" · ")}\n` : "";
  if (kind === "report") return head + subj + `이 사진은 ${c("date")} 하루의 수업 필기·보고서야. 날짜별 수업 보고서 형식으로 옮겨.
- classes: 과목별로 오늘 배운 내용 (subject = 과목, text = 배운 내용, 단원·핵심 개념·예제). 과목을 알 수 없으면 내용으로 짐작하고, 그래도 모르면 "".
- important: 선생님이 강조한 것, 시험에 나온다고 한 것
- memorize: 외워야 할 것 (단어, 공식, 연도 등)
- remember: 기억해야 할 것 (숙제, 준비물, 수행평가·시험 날짜 — 날짜가 있으면 "11/20 영어 수행" 처럼 앞에)
- etc: 그 밖의 메모`;
  if (kind === "note") return head + subj + `이 사진은 날짜와 상관없는 공부 정리(단원 정리, 필기, 요약)야. 자유 보고서 형식으로 옮겨.
- title: 사진의 제목이나 주제 (없으면 내용을 보고 짧게 지어도 돼)
- subject: 과목 (모르면 "")
- body: 정리한 내용 본문 (구조 그대로)
- important / memorize / remember / etc: 강조된 것 / 외울 것 / 기억할 것(숙제·날짜) / 기타 — 사진에서 그렇게 표시된 것만`;
  if (kind === "exam") return head + subj + `이 사진은 시험 범위표(정기시험 공지, 과목별 시험 범위, 시간표) 또는 수행평가 안내야. 시험 형식으로 옮겨.
- kind: 여러 과목의 중간·기말·정기 시험이면 "정기", 한 과목의 수행평가면 "수행".
- 정기: name = 시험 이름(예: 2학기 기말고사), date = 시작일, end = 마지막 날, subjects = 과목마다 { subject, date(그 과목 시험 보는 날, 모르면 ""), ranges = 범위를 단원·쪽 단위로 나눈 목록 (예: "Ⅲ. 해수의 순환 p.80~95", "프린트 1~5") }. ranges 는 짧은 항목 여러 개로 나눠.
- 수행: subject, name(수행평가 이름), date, ranges(평가 범위·내용). 이때 subjects 는 [].
- 정기일 때 subject 는 "", ranges 는 [].
- memo: 시험 방식, 준비물, 배점, 유의 사항 등 그 밖의 내용.`;
  // plan
  const month = ctx.view === "month";
  return head + `이 사진은 공부 계획표(${month ? "월간" : "주간"} 플래너, 시간표, 할 일 목록)야. 계획표 형식으로 옮겨.
이 화면의 날짜 범위: ${c("from")} ~ ${c("to")} (이 범위 밖의 날짜는 넣지 마)
- days: 날짜마다 { date, events = 시간이 있는 일정 [{start, end(없으면 ""), title}], tasks = 시간 없는 할 일·메모 }. 내용이 있는 날만 넣어. 요일만 적혀 있으면 이 범위 안의 그 요일 날짜로.
- 완료 표시(체크·줄 긋기)된 할 일은 앞에 "✅ " 를 붙여.
${month ? "- goal: 이달의 목표 (한 줄에 하나), memo: 이달 메모. grit, must 는 []." : `- grit: 과목별 이번 주 목표 [{subject, content, day(요일, 예: "월·수")}] — 'GRIT' 이나 과목별 목표 표가 있을 때만.
- must: 'MUST DO' 나 이번 주 꼭 할 것 목록. goal, memo 는 [].`}`;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "POST 만 돼요" }, 405);

  // 🔒 로그인한 사람만
  const jwt = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  const url = Deno.env.get("SUPABASE_URL")!, anon = Deno.env.get("SUPABASE_ANON_KEY")!;
  const { data: u, error: ue } = await createClient(url, anon).auth.getUser(jwt);
  if (ue || !u?.user) return json({ error: "로그인이 필요해요" }, 401);
  const uid = u.user.id;

  const key = Deno.env.get("ANTHROPIC_API_KEY");
  if (!key) return json({ error: "서버에 ANTHROPIC_API_KEY 가 없어요 (SUPABASE_SETUP.md 참고)", code: "no_key" }, 500);

  let body: { kind?: string; images?: { data?: string; media_type?: string }[]; context?: Record<string, unknown> };
  try { body = await req.json(); } catch { return json({ error: "요청 형식이 틀렸어요" }, 400); }
  const kind = String(body.kind || "");
  if (!SCHEMAS[kind]) return json({ error: "모르는 종류예요: " + kind }, 400);
  const images = (body.images || []).slice(0, MAX_IMAGES);
  if (!images.length) return json({ error: "사진이 없어요" }, 400);
  for (const im of images)
    if (!MEDIA.has(String(im.media_type)) || typeof im.data !== "string" || !im.data || im.data.length > MAX_B64)
      return json({ error: "사진 형식이나 크기가 맞지 않아요" }, 400);

  // 🔒 하루 사용 횟수 제한 (supabase/ai_scan.sql 의 ai_scans 표. 표가 없으면 제한 없이)
  const svc = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const admin = svc ? createClient(url, svc) : null;
  if (admin) {
    const since = new Date(Date.now() - 864e5).toISOString();
    const { count, error } = await admin.from("ai_scans").select("id", { count: "exact", head: true }).eq("user_id", uid).gte("created_at", since);
    if (!error && (count ?? 0) >= DAILY_LIMIT) return json({ error: `오늘은 사진 인식을 ${DAILY_LIMIT}번 다 썼어요. 내일 다시 해 주세요.`, code: "limit" }, 429);
  }

  const client = new Anthropic({ apiKey: key });
  try {
    const res = await client.beta.messages.create({
      model: MODEL,
      max_tokens: 16000,
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",   // 안전 필터가 거절하면 서버에서 다른 모델로 한 번 더
      output_config: { effort: "medium", format: { type: "json_schema", schema: SCHEMAS[kind] } },
      system: prompt(kind, body.context || {}),
      messages: [{
        role: "user",
        content: [
          ...images.map((im) => ({ type: "image" as const, source: { type: "base64" as const, media_type: im.media_type as "image/jpeg", data: im.data! } })),
          { type: "text" as const, text: images.length > 1 ? `사진 ${images.length}장을 순서대로 이어서 읽고 하나로 합쳐 옮겨 줘.` : "이 사진을 읽고 옮겨 줘." },
        ],
      }],
    });
    if (res.stop_reason === "refusal") return json({ error: "이 사진은 읽을 수 없어요 (AI 가 거절했어요)" }, 422);
    if (res.stop_reason === "max_tokens") return json({ error: "내용이 너무 길어요. 사진을 나눠서 해 주세요." }, 422);
    const text = res.content.filter((b) => b.type === "text").map((b) => (b as { text: string }).text).join("");
    let result: unknown;
    try { result = JSON.parse(text); } catch { return json({ error: "AI 결과를 읽지 못했어요. 다시 해 주세요." }, 502); }
    if (admin) await admin.from("ai_scans").insert({ user_id: uid, kind }).then(() => {}, () => {});
    return json({ result });
  } catch (e) {
    if (e instanceof Anthropic.RateLimitError) return json({ error: "AI 가 바빠요. 잠시 뒤에 다시 해 주세요." }, 429);
    if (e instanceof Anthropic.AuthenticationError) return json({ error: "서버의 ANTHROPIC_API_KEY 가 틀렸어요", code: "bad_key" }, 500);
    if (e instanceof Anthropic.BadRequestError) { console.error(e.message); return json({ error: "사진을 보낼 수 없었어요 (" + e.message.slice(0, 120) + ")" }, 400); }
    if (e instanceof Anthropic.APIConnectionError) return json({ error: "AI 서버에 연결하지 못했어요" }, 502);
    if (e instanceof Anthropic.APIError) { console.error(e.status, e.message); return json({ error: "AI 서버 오류예요. 잠시 뒤에 다시 해 주세요." }, 502); }
    console.error(e);
    return json({ error: "알 수 없는 오류예요" }, 500);
  }
});
