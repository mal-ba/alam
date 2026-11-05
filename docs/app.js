"use strict";
const OWNER = "mal-ba", REPO = "alam";
const WD = ["일","월","화","수","목","금","토"];
const HOW_TO_EDIT = `> **고치는 법** (오른쪽 위 연필 ✏️ 버튼 → 수정 → Commit changes)
> - \`일정\` 칸: \`시간 제목\`을 쉼표(\`,\`)로 구분해서 적어요. 시간이 있는 일정은 알람이 와요.
>   - 예) \`08:45 등교, 18:00~21:00 야자, 19:00 친구 생일 [60,10]\`
>   - 끝에 \`[60,10]\`처럼 쓰면 60분 전·10분 전에 알림 (안 쓰면 기본값)
>   - \`[0]\`은 정각에 알림, \`[]\`는 알림 없음
> - \`할 일·메모\` 칸: 시간 없이 적고 싶은 것 (아침 요약 알림에 같이 와요)
> - 그날 일정을 다 지우면 그날은 일정 없음으로 처리돼요.
`;

/* ---------- 저장소(브라우저) ---------- */
function store(k, v) {
  try {
    if (v === undefined) return localStorage.getItem("alam." + k);
    if (v === null) localStorage.removeItem("alam." + k); else localStorage.setItem("alam." + k, v);
  } catch (e) { return null; }
}

/* ---------- 날짜 ---------- */
const pad = n => String(n).padStart(2, "0");
const D = s => { const [y, m, d] = s.split("-").map(Number); return new Date(Date.UTC(y, m - 1, d)); };
const iso = dt => dt.toISOString().slice(0, 10);
const addDays = (s, n) => { const d = D(s); d.setUTCDate(d.getUTCDate() + n); return iso(d); };
const wday = s => D(s).getUTCDay();               // 0=일
const pyWd = s => (wday(s) + 6) % 7;              // schedule.json: 0=월
const weekStart = s => addDays(s, -wday(s));
const monthFirst = s => s.slice(0, 8) + "01";
const weekPath = s => `plans/week/${weekStart(s)}.md`;
const monthPath = s => `plans/month/${s.slice(0, 7)}.md`;
const todayKST = () => iso(new Date(Date.now() + 9 * 3600e3));
const mmdd = s => `${s.slice(5, 7)}/${s.slice(8, 10)}`;
function monthDays(s) {
  const out = []; let c = monthFirst(s);
  while (c.slice(0, 7) === s.slice(0, 7)) { out.push(c); c = addDays(c, 1); }
  return out;
}

/* ---------- GitHub API ---------- */
let token = store("token"), branch = null, schedule = null;
const files = new Map();   // path -> {text, sha} | null

async function api(path, opts = {}) {
  const headers = { "Accept": "application/vnd.github+json", "Authorization": "Bearer " + token };
  if (opts.body) headers["Content-Type"] = "application/json";
  const r = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}${path}`, { ...opts, headers });
  if (r.status === 404 && !opts.method) return null;   // 읽기: 파일 없음
  if (!r.ok) {
    const t = await r.text();
    const e = new Error(`${r.status} ${t.slice(0, 200)}`); e.status = r.status; throw e;
  }
  return r.json();
}
const b64d = s => new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\s/g, "")), c => c.charCodeAt(0)));
function b64e(s) {
  const b = new TextEncoder().encode(s); let o = "";
  for (let i = 0; i < b.length; i += 0x8000) o += String.fromCharCode(...b.subarray(i, i + 0x8000));
  return btoa(o);
}
/* ---------- 저장소: Supabase(로그인한 계정 것만) 또는 예전 GitHub 파일 ---------- */
const CFG = window.ALAM_CONFIG || {};
const SB = CFG.supabaseUrl && CFG.supabaseAnonKey && window.supabase
  ? window.supabase.createClient(CFG.supabaseUrl, CFG.supabaseAnonKey, { auth: { persistSession: true, detectSessionInUrl: true, flowType: "pkce" } })
  : null;
if (SB && token) { store("token", null); token = null; }   // 🔒 Supabase 를 쓰면 예전 GitHub 토큰은 필요 없어요 → 기기에 남기지 않기
let sbUser = null, sbAll = false;   // sbAll: 내 문서를 한 번에 다 받아 둠 (캐시가 곧 전부)
function sbErr(error) {
  const e = new Error(error.message || String(error));
  e.status = /JWT|auth|401/i.test(error.message || "") ? 401 : error.code === "42501" ? 403 : (error.status || 0);
  return e;
}
async function sbLoadAll() {
  files.clear();
  const { data, error } = await SB.from("docs").select("path,content,updated_at").limit(10000);
  if (error) throw sbErr(error);
  for (const r of data) files.set(r.path, { text: r.content, sha: r.updated_at });
  sbAll = true;
}
async function getFile(path, force) {
  if (!force && files.has(path)) return files.get(path);
  if (SB && sbAll && !force) return null;
  let f;
  if (SB) {
    const { data, error } = await SB.from("docs").select("content,updated_at").eq("path", path).maybeSingle();
    if (error) throw sbErr(error);
    f = data ? { text: data.content, sha: data.updated_at } : null;
  } else {
    const j = await api(`/contents/${path}?ref=${encodeURIComponent(branch)}&_=${Date.now()}`);
    f = j ? { text: b64d(j.content), sha: j.sha } : null;
  }
  if (f) files.set(path, f); else if (SB) files.delete(path); else files.set(path, null);
  return f;
}
// fn(현재내용|null) -> 새 내용. 충돌(다른 곳에서 먼저 저장)이면 최신본으로 한 번 더 시도
async function updateFile(path, fn, message) {
  if (SB) {
    const cur = await getFile(path);
    const text = fn(cur ? cur.text : null);
    if (cur && text === cur.text) return;
    const { data, error } = await SB.from("docs")
      .upsert({ user_id: sbUser.id, path, content: text, updated_at: new Date().toISOString() }, { onConflict: "user_id,path" })
      .select("updated_at").single();
    if (error) throw sbErr(error);
    files.set(path, { text, sha: data.updated_at }); return;
  }
  for (let attempt = 0; attempt < 2; attempt++) {
    const cur = await getFile(path, attempt > 0);
    const text = fn(cur ? cur.text : null);
    if (cur && text === cur.text) return;
    try {
      const j = await api(`/contents/${path}`, { method: "PUT",
        body: JSON.stringify({ message, content: b64e(text), branch, ...(cur ? { sha: cur.sha } : {}) }) });
      files.set(path, { text, sha: j.content.sha }); return;
    } catch (e) {
      if (attempt === 0 && (e.status === 409 || e.status === 422)) continue;
      throw e;
    }
  }
}
async function listDir(dir) {   // 폴더 안 파일 이름들
  if (SB) {
    if (!sbAll) await sbLoadAll();
    return [...files.keys()].filter(p => p.startsWith(dir + "/") && files.get(p)).map(p => p.slice(dir.length + 1)).filter(n => !n.includes("/"));
  }
  const list = await api(`/contents/${dir}?ref=${encodeURIComponent(branch)}&_=${Date.now()}`);
  return (Array.isArray(list) ? list : []).map(f => f.name);
}
async function deleteFile(path, message) {
  if (SB) {
    const { error } = await SB.from("docs").delete().eq("path", path);
    if (error) throw sbErr(error);
  } else {
    const f = await getFile(path, true);
    if (f) await api(`/contents/${path}`, { method: "DELETE", body: JSON.stringify({ message, sha: f.sha, branch }) });
  }
  files.delete(path);
}

/* ---------- 표 읽고 쓰기 (alarm.py 와 같은 형식) ---------- */
const EV = /^(\d{1,2}):(\d{2})(?:\s*[~\-]\s*(\d{1,2}):(\d{2}))?\s+(.+?)\s*(?:\[([\d,\s]*)\])?$/;
const splitItems = c => c.split(/,(?![^\[]*\])/).map(s => s.trim()).filter(Boolean);
function rowDate(line, refIso) {
  const t = line.trim(); if (!t.startsWith("|")) return null;
  const cells = t.replace(/^\|/, "").replace(/\|$/, "").split("|").map(c => c.trim());
  const m = cells[0].match(/^(\d{1,2})\s*\/\s*(\d{1,2})/);
  if (!m || cells.length < 2) return null;
  const ry = +refIso.slice(0, 4), rm = +refIso.slice(5, 7), mo = +m[1];
  return { key: `${ry + (mo < rm ? 1 : 0)}-${pad(mo)}-${pad(+m[2])}`, cells };
}
function parseTable(text, refIso) {
  const out = {}; if (!text) return out;
  for (const line of text.split("\n")) {
    const r = rowDate(line, refIso);
    if (r) out[r.key] = parseCells(r.cells[1], r.cells[2] || "");
  }
  return out;
}
function parseCells(ec, mc) {
  const events = [], memos = [];
  for (const it of splitItems(ec)) {
    const m = it.match(EV);
    if (!m) { memos.push(it); continue; }
    events.push({ start: pad(+m[1]) + ":" + m[2], end: m[3] ? pad(+m[3]) + ":" + m[4] : "", title: m[5],
      remind: m[6] == null ? null : m[6].replace(/\s/g, "").split(",").filter(Boolean).map(Number) });
  }
  memos.push(...splitItems(mc));
  events.sort((a, b) => a.start.localeCompare(b.start));
  return { events, memos };
}
function defaultRemind(title) {
  for (const evs of Object.values(schedule.weekly))
    for (const e of evs) if (e.title === title) return e.remind_before || [0];
  return schedule.default_remind_before || [10];
}
const remindText = r => r.length ? r.map(x => x === 0 ? "정각" : x + "분 전").join(", ") : "알림 없음";
function formatEvent(e) {
  let t = `${e.end ? e.start + "~" + e.end : e.start} ${e.title}`;
  if (e.remind && JSON.stringify(e.remind) !== JSON.stringify(defaultRemind(e.title))) t += ` [${e.remind.join(",")}]`;
  return t;
}
const formatRow = (s, day) =>
  `| ${mmdd(s)} (${WD[wday(s)]}) | ${day.events.map(formatEvent).join(", ")} | ${day.memos.join(", ")} |`;
function replaceRows(text, refIso, rows) {
  return text.split("\n").map(line => { const r = rowDate(line, refIso); return r && rows[r.key] ? rows[r.key] : line; }).join("\n");
}
function newTable(title, dayList, rows) {
  return [`# ${title}`, "", HOW_TO_EDIT, "| 날짜 | 일정 | 할 일·메모 |", "|---|---|---|", ...dayList.map(s => rows[s])].join("\n") + "\n";
}
// ---- 학교: 휴업일·방학·시간표 (alarm.py 와 같은 규칙)
const school = () => schedule.school || {};
function schoolOff(s) {
  const off = (school().off_days || {})[s]; if (off) return off;
  for (const v of school().vacations || []) if (v.from <= s && s <= v.to) return v.name;
  return null;
}
const examOf = s => (school().exam_days || {})[s] || null;
function classesOf(s) {
  const sc = school();
  if (schoolOff(s) || examOf(s) || (sc.timetable_until && s > sc.timetable_until)) return [];
  const subj = [...((sc.timetable || {})[String(pyWd(s))] || [])];
  const alt = sc.alternating;
  if (alt && pyWd(s) === alt.weekday && subj.length) {
    const n = Math.round((D(weekStart(s)) - D(weekStart(alt.ref_date))) / 864e5 / 7);
    const pick = alt.options[((n % alt.options.length) + alt.options.length) % alt.options.length];
    for (const p of alt.periods) if (p <= subj.length) subj[p - 1] = pick;
  }
  return subj;
}
function baseDay(s) {
  let events = (schedule.weekly[String(pyWd(s))] || []).map(e => ({ start: e.start, end: e.end || "", title: e.title, remind: null }));
  const memos = [], off = schoolOff(s);
  if (off) {
    const st = new Set(school().school_events || []);
    events = events.filter(e => !st.has(e.title));
    memos.push(`🏫 ${off} - 학교 안 감`);
  } else if (examOf(s)) {
    const keep = new Set(school().exam_keep_events || ["등교"]);
    const st = new Set((school().school_events || []).filter(t => !keep.has(t)));
    events = events.filter(e => !st.has(e.title));
    memos.push(`✏️ ${examOf(s)} - 등교만 (하교·야자 없음)`);
  }
  const note = (school().notes || {})[s]; if (note) memos.push(note);
  return { events, memos: memos.map(m => m.replace(/,/g, "·").replace(/\|/g, " ")) };
}
async function resolveDay(s) {
  const w = await getFile(weekPath(s)); const wt = w && parseTable(w.text, weekStart(s));
  if (wt && wt[s]) return wt[s];
  const m = await getFile(monthPath(s)); const mt = m && parseTable(m.text, monthFirst(s));
  if (mt && mt[s]) return mt[s];
  return baseDay(s);
}

/* ---------- 화면 상태 ---------- */
const MODES = ["today", "week", "month", "year", "report", "exam", "books", "map", "news", "notice", "learn", "web", "weak"];
let mode = MODES.includes(store("mode")) ? store("mode") : "today";
const weekish = () => mode === "week" || mode === "today";   // '오늘'은 주간 표를 읽고 그날만 보여줌
let anchor = todayKST();
{ // 알림에서 열면 ?report=YYYY-MM-DD → 그날 보고서 탭
  const qs = new URLSearchParams(location.search), q = qs.get("report"), qd = qs.get("day");
  if (qs.has("v")) history.replaceState(null, "", location.pathname);
  if (MODES.includes(qs.get("mode"))) { mode = qs.get("mode"); history.replaceState(null, "", location.pathname); }
  if (q && /^\d{4}-\d{2}-\d{2}$/.test(q)) { mode = "report"; anchor = q; store("rkind", "date"); history.replaceState(null, "", location.pathname); }
  else if (qd && /^\d{4}-\d{2}-\d{2}$/.test(qd)) { mode = "today"; anchor = qd; history.replaceState(null, "", location.pathname); }
}
let days = [];        // [{iso, day}]
let editing = null;   // {i, draft}  ✏️ 를 누른 날 하나만 수정 가능
let secEdit = null;   // {key, draft}  목표·MEMO·GRIT 수정 중
let saving = false;
let fileExists = false;
let viewText = null;  // 지금 보고 있는 주간/월간 파일 내용
let selDay = null;    // 월간 달력에서 고른 날짜

const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
// 🔒 밖에서 들어온 주소(뉴스 RSS 등)는 http(s) 만 링크로 — javascript: 같은 주소는 막아요
const safeUrl = u => { try { const x = new URL(String(u || ""), location.href); return /^https?:$/.test(x.protocol) ? x.href : "#"; } catch (e) { return "#"; } };
function toast(msg, ms = 2500) { const t = $("toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove("show"), ms); }
const WD_EN = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
const isSys = m => /^(🏫|✏️)/.test(m);           // 학교 일정에서 자동으로 생긴 메모 (체크박스 없음)
const isDone = m => m.startsWith("✅");
const taskText = m => m.replace(/^✅\s*/, "");
const cleanText = t => (t || "").replace(/[,]/g, "·").replace(/[|\[\]]/g, " ").replace(/\s+/g, " ").trim();

function clean(day) {
  const events = [];
  for (const e of day.events) {
    const title = cleanText(e.title);
    if (!title) continue;
    if (!e.start) { (day.tasks ||= []).push({ text: title, done: false }); continue; }
    events.push({ start: e.start, end: e.end || "", title, remind: e.remind });
  }
  const memos = day.tasks
    ? day.tasks.map(t => ({ ...t, text: cleanText(t.text) })).filter(t => t.text).map(t => (t.done ? "✅ " : "") + t.text)
    : day.memos.map(m => m.replace(/[,|]/g, "·").trim()).filter(Boolean);
  events.sort((a, b) => a.start.localeCompare(b.start));
  return { events, memos };
}
const viewPath = () => weekish() ? weekPath(anchor) : monthPath(anchor);
const viewRef = () => weekish() ? weekStart(anchor) : monthFirst(anchor);
const viewDays = () => weekish() ? Array.from({ length: 7 }, (_, i) => addDays(weekStart(anchor), i)) : monthDays(anchor);
const viewTitle = () => {
  if (weekish()) { const s = weekStart(anchor), e = addDays(s, 6); return `주간 계획표 (${s.replace(/-/g, ".")} 일 ~ ${e.slice(5).replace("-", ".")} 토)`; }
  return `${+anchor.slice(0, 4)}년 ${+anchor.slice(5, 7)}월 계획표`;
};
const editDirty = () => !!secEdit || !!noteDraft || !!examDraft || !!tbDraft || !!placeDraft || !!weakDraft
  || (repDraft && buildReport(anchor, repDraft) !== buildReport(anchor, rep.data))
  || (editing && formatRow(days[editing.i].iso, clean(editing.draft)) !== formatRow(days[editing.i].iso, days[editing.i].day));
const leaveOk = () => !editDirty() || confirm("수정 중인 내용이 저장되지 않았어요. 그래도 나갈까요?");

/* ---------- 표 안의 목표·MEMO·GRIT 칸 (## 제목 아래 내용) ---------- */
const SEC = { goal: "🎯 이달의 목표", memo: "🗒️ MEMO", grit: "💪 GRIT", must: "✅ MUST DO" };
const SEC_END = /^## |^> \*\*고치는|^\| 날짜/;
function getSection(text, name) {
  if (!text) return [];
  const lines = text.split("\n"), s = lines.findIndex(l => l.trim() === `## ${name}`);
  if (s < 0) return [];
  const out = [];
  for (let i = s + 1; i < lines.length && !SEC_END.test(lines[i]); i++) if (lines[i].trim()) out.push(lines[i].trim());
  return out;
}
function setSection(text, name, body) {
  const lines = text.split("\n"), s = lines.findIndex(l => l.trim() === `## ${name}`);
  const block = [`## ${name}`, "", ...body, ""];
  if (s >= 0) { let e = s + 1; while (e < lines.length && !SEC_END.test(lines[e])) e++; lines.splice(s, e - s, ...block); }
  else { let at = lines.findIndex(l => /^> \*\*고치는|^\| 날짜/.test(l)); if (at < 0) at = lines.length; lines.splice(at, 0, ...block); }
  return lines.join("\n").replace(/\n{3,}/g, "\n\n");
}
const listOf = (text, name) => getSection(text, name).map(l => l.replace(/^[-*]\s*/, ""));
function gritOf(text) {
  return getSection(text, SEC.grit).filter(l => l.startsWith("|") && !/^\|\s*과목|^\|\s*-/.test(l)).map(l => {
    const c = l.replace(/^\||\|$/g, "").split("|").map(x => x.trim());
    return { subject: c[0] || "", content: c[1] || "", day: c[2] || "" };
  });
}
const GRIT_DEFAULT = ["수학", "영어", "과학", "사회", "국어", "역사"];

/* ---------- 불러오기 ---------- */
function showsToday() {
  const t = todayKST();
  if (mode === "week") return weekStart(anchor) === weekStart(t);
  if (mode === "month") return anchor.slice(0, 7) === t.slice(0, 7);
  if (mode === "year") return anchor.slice(0, 4) === t.slice(0, 4);
  return anchor === t;   // 오늘, 보고서
}
let loadSeq = 0;   // 탭을 빨리 바꿀 때, 늦게 끝난 예전 불러오기가 새 화면을 덮지 않게
async function load() {
  const seq = ++loadSeq;
  editing = null; repDraft = null; secEdit = null; weakDraft = null;
  const free = (mode === "report" && reportKind !== "date") || mode === "exam" || mode === "books" || mode === "map" || mode === "news" || mode === "notice" || mode === "learn" || mode === "web" || mode === "weak";
  $("goToday").hidden = free || showsToday();
  $("prev").style.visibility = $("next").style.visibility = free ? "hidden" : "";
  document.querySelectorAll(".tabs button[data-mode], #moreMenu button").forEach(b => b.setAttribute("aria-selected", b.dataset.mode === mode));
  const more = { exam: "📝 시험", books: "📚 출판사", year: "📆 연간", map: "🗺️ 지도", news: "📰 뉴스", learn: "💻 코딩", web: "🔎 검색", weak: "🩹 약점" }[mode];
  $("moreBtn").textContent = more ? more + " ▾" : "☰ 메뉴";
  $("moreBtn").setAttribute("aria-selected", !!more);
  $("noticeBtn").setAttribute("aria-pressed", mode === "notice");
  if (mode === "report") return loadReport(seq);
  if (mode === "year") return loadYear(seq);
  if (mode === "exam") return loadExams(seq);
  if (mode === "books") return loadBooks(seq);
  if (mode === "map") return loadMap(seq);
  if (mode === "news") return loadNews(seq);
  if (mode === "notice") return loadNotice(seq);
  if (mode === "learn") return loadLearn(seq);
  if (mode === "web") return loadWeb(seq);
  if (mode === "weak") return loadWeak(seq);
  const s = weekStart(anchor);
  $("label").innerHTML = mode === "today"
    ? `${mmdd(anchor)} (${WD[wday(anchor)]})<span class="sub">${anchor === todayKST() ? "오늘 일정" : "하루 일정"}</span>`
    : mode === "week"
    ? `${mmdd(s)} ~ ${mmdd(addDays(s, 6))}<span class="sub">WEEKLY STUDY PLAN</span>`
    : `${+anchor.slice(0, 4)}년 ${+anchor.slice(5, 7)}월<span class="sub">${["JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE","JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER"][+anchor.slice(5, 7) - 1]}</span>`;
  $("view").innerHTML = `<div class="loading">불러오는 중…</div>`;
  try {
    const f = await getFile(viewPath());
    const list = [];
    for (const d of viewDays()) list.push({ iso: d, day: clean(await resolveDay(d)) });
    await loadReportList();
    if (mode === "month") await loadExamData();
    if (seq !== loadSeq) return;
    fileExists = !!f; viewText = f ? f.text : null; days = list;
    if (mode === "month" && (!selDay || selDay.slice(0, 7) !== anchor.slice(0, 7)))
      selDay = anchor.slice(0, 7) === todayKST().slice(0, 7) ? todayKST() : monthFirst(anchor);
    render();
  } catch (e) { if (seq === loadSeq) showError(e); }
}

const spanOf = e => e.end ? `${e.start}~${e.end}` : e.start;
function remindShort(e) {
  const r = e.remind ?? defaultRemind(e.title);
  return r.length ? "🔔 " + r.map(x => x === 0 ? "정각" : x + "분").join("·") : "🔕";
}
const inVacation = s => (school().vacations || []).some(v => v.from <= s && s <= v.to);
const dateCls = s => { const w = wday(s); return w === 0 || (school().off_days || {})[s] ? "sun" : w === 6 ? "sat" : inVacation(s) ? "vac" : ""; };

/* ---------- 하루 칸 ---------- */
function dayCard(i) {
  if (!days[i]) return "";
  const d = days[i], today = todayKST(), w = wday(d.iso), ed = editing && editing.i === i;
  const label = mode === "week"
    ? `<span class="jak">작심${i + 1}일</span><span class="date ${dateCls(d.iso)}">${+d.iso.slice(5, 7)}.${+d.iso.slice(8)} ${WD_EN[w]}</span>`
    : `<span class="date ${dateCls(d.iso)}">${mmdd(d.iso)} (${WD[w]})</span>`;
  const head = `<div class="dhead">${label}
    ${d.iso === today ? '<span class="badge">오늘</span>' : ""}<span class="sp"></span>
    ${ed ? "" : `<button class="repbtn${reportSet.has(d.iso) ? " has" : ""}" data-act="report">📒 보고서</button>
    <button class="pencil" data-act="edit" aria-label="${mmdd(d.iso)} 수정" title="수정">✏️</button>`}</div>`;
  if (!ed) {
    const evs = d.day.events.map(e => `<li><span class="t">${spanOf(e)}</span><span>${esc(e.title)}</span><span class="r">${remindShort(e)}</span></li>`).join("");
    const notes = d.day.memos.map((m, k) => isSys(m) ? `<li class="memo-i">${esc(m)}</li>`
      : `<li class="task${isDone(m) ? " done" : ""}"><button class="chk${isDone(m) ? " on" : ""}" data-act="chk" data-k="${k}" aria-label="완료 표시">${isDone(m) ? "✓" : ""}</button><span>${esc(taskText(m))}</span></li>`).join("");
    const cls = classesOf(d.iso), times = school().period_times || [];
    const clsHtml = !cls.length ? "" : mode === "today"
      ? `<div class="rsec"><h3>📚 시간표</h3><ul class="list">${cls.map((c, k) => `<li><span class="t">${k + 1}교시 ${times[k] || ""}</span><span>${esc(c)}</span></li>`).join("")}</ul></div>`
      : `<div class="classes">📚 ${cls.map((c, k) => `${"①②③④⑤⑥⑦⑧⑨"[k] || k + 1}<b>${esc(c)}</b>`).join(" · ")}</div>`;
    return `<section class="day${mode === "week" ? " box" : ""}${d.iso < today ? " past" : ""}" data-i="${i}">${head}
      ${evs ? `<ul class="list">${evs}</ul>` : ""}
      ${notes ? `<ul class="list tasks">${notes}</ul>` : ""}
      ${!evs && !notes ? '<div class="empty">일정 없음</div>' : ""}${clsHtml}</section>`;
  }
  const dr = editing.draft;
  return `<section class="day editing" data-i="${i}">${head}
    <div class="body">
      <div class="lbl">⏰ 일정 (시간이 있으면 알람이 와요)</div>
      ${dr.events.map((e, j) => `<div class="ev" data-j="${j}">
        <div class="times"><input type="time" data-f="start" value="${e.start}" aria-label="시작">~<input type="time" data-f="end" value="${e.end}" aria-label="끝(선택)"></div>
        <input class="title" data-f="title" value="${esc(e.title)}" placeholder="일정 이름">
        <div class="remind">🔔<input data-f="remind" value="${e.remind == null ? "" : e.remind.length ? e.remind.join(",") : "없음"}"
           placeholder="기본: ${esc(remindText(defaultRemind(e.title || "")))}" aria-label="몇 분 전 알림">분 전</div>
        <button class="del" data-act="del" aria-label="삭제">×</button></div>`).join("")}
      <button class="add" data-act="add">+ 일정 추가</button>
      <div class="lbl">☑️ 할 일·메모</div>
      ${dr.tasks.map((t, k) => `<div class="trow" data-k="${k}">
        <button class="chk${t.done ? " on" : ""}" data-act="tchk" aria-label="완료">${t.done ? "✓" : ""}</button>
        <input data-t="text" value="${esc(t.text)}" placeholder="예) 수학 쎈 p.30~35">
        <button class="del" data-act="tdel" aria-label="삭제">×</button></div>`).join("")}
      <button class="add" data-act="tadd">+ 할 일 추가</button>
      <div class="actions">
        <button class="btn ghost" data-act="cancel" ${saving ? "disabled" : ""}>취소</button>
        <button class="btn" data-act="save" ${saving ? "disabled" : ""}>${saving ? "저장 중…" : "저장"}</button>
      </div>
    </div></section>`;
}

/* ---------- 목표·MEMO·GRIT 카드 ---------- */
function secHead(title, key) {
  return `<div class="dhead"><span class="date">${title}</span><span class="sp"></span>
    ${secEdit && secEdit.key === key ? "" : `<button class="pencil" data-act="sedit" data-key="${key}" aria-label="${title} 수정">✏️</button>`}</div>`;
}
const secActions = () => `<div class="actions" style="margin-top:10px">
  <button class="btn ghost" data-act="scancel" ${saving ? "disabled" : ""}>취소</button>
  <button class="btn" data-act="ssave" ${saving ? "disabled" : ""}>${saving ? "저장 중…" : "저장"}</button></div>`;
function listCard(key, title, empty) {
  const ed = secEdit && secEdit.key === key, items = listOf(viewText, SEC[key]);
  return `<section class="day sec ${key}${ed ? " editing" : ""}">${secHead(title, key)}
    ${ed ? `<textarea class="sbox" data-s="text" placeholder="한 줄에 하나씩">${esc(secEdit.draft)}</textarea>${secActions()}`
      : items.length ? `<ul class="blist">${items.map(x => `<li>${esc(x)}</li>`).join("")}</ul>` : `<div class="empty">${empty}</div>`}</section>`;
}
function gritCard() {
  const ed = secEdit && secEdit.key === "grit";
  const rows = gritOf(viewText), must = listOf(viewText, SEC.must);
  if (ed) {
    const g = secEdit.draft;
    return `<section class="day sec grit editing">${secHead("💪 GRIT", "grit")}
      <div class="lbl">과목별 이번 주 목표</div>
      ${g.rows.map((r, k) => `<div class="grow" data-k="${k}">
        <input data-g="subject" value="${esc(r.subject)}" placeholder="과목" list="subjects">
        <input data-g="content" value="${esc(r.content)}" placeholder="내용 (예: 쎈 B단계 30쪽)">
        <input data-g="day" value="${esc(r.day)}" placeholder="요일">
        <button class="del" data-act="gdel" aria-label="삭제">×</button></div>`).join("")}
      <button class="add" data-act="gadd">+ 과목 추가</button>
      <div class="lbl">MUST DO (한 줄에 하나씩)</div>
      <textarea class="sbox" data-s="must" placeholder="이번 주에 꼭 할 것">${esc(g.must)}</textarea>
      <datalist id="subjects">${[...new Set([...GRIT_DEFAULT, ...Object.values(school().timetable || {}).flat()])].map(x => `<option value="${esc(x)}">`).join("")}</datalist>
      ${secActions()}</section>`;
  }
  return `<section class="day sec grit">${secHead("💪 GRIT", "grit")}
    ${rows.length ? `<table class="gtab"><thead><tr><th>SUBJECT</th><th>CONTENT</th><th>DAY</th></tr></thead><tbody>
      ${rows.map(r => `<tr><td>${esc(r.subject)}</td><td>${esc(r.content)}</td><td>${esc(r.day)}</td></tr>`).join("")}</tbody></table>`
      : '<div class="empty">✏️을 눌러 이번 주 과목별 목표를 적어 보세요.</div>'}
    <div class="must"><b>MUST DO</b>${must.length ? `<ul class="blist">${must.map(x => `<li>${esc(x)}</li>`).join("")}</ul>` : '<span class="empty"> -</span>'}</div></section>`;
}

/* ---------- 월간 달력 ---------- */
function monthGrid() {
  const today = todayKST(), first = monthFirst(anchor), lead = wday(first);
  const cells = [];
  for (let k = 0; k < lead; k++) cells.push('<div class="cell blank"></div>');
  const st = new Set(school().school_events || []);
  days.forEach((d, i) => {
    const items = [
      ...d.day.memos.filter(m => !isDone(m)).map(m => `<span class="ci${isSys(m) ? " sys" : ""}">${esc(taskText(m).replace(/ - .*$/, "").replace(/^🏫 |^✏️ /, ""))}</span>`),
      ...examsOn(d.iso).map(x => `<span class="ci xm">📝${esc(x.subject || x.name)}</span>`),
      ...d.day.events.filter(e => !st.has(e.title)).map(e => `<span class="ci ce">${esc(e.title)}</span>`),
    ];
    const cls = ["cell", dateCls(d.iso), d.iso === today ? "today" : "", d.iso === selDay ? "sel" : "", examOf(d.iso) ? "exam" : "", schoolOff(d.iso) ? "off" : ""].join(" ");
    cells.push(`<button class="${cls}" data-act="pick" data-i="${i}"><span class="n">${+d.iso.slice(8)}</span>${items.slice(0, 3).join("")}${items.length > 3 ? `<span class="ci more">+${items.length - 3}</span>` : ""}${reportSet.has(d.iso) ? '<i class="rdot"></i>' : ""}</button>`);
  });
  return `<section class="day cal"><div class="cal-h">${WD.map((x, k) => `<span class="${k === 0 ? "sun" : k === 6 ? "sat" : ""}">${x}</span>`).join("")}</div>
    <div class="cal-g">${cells.join("")}</div></section>`;
}

/* ---------- 연간 ---------- */
async function loadYear(seq = loadSeq) {
  const Y = +anchor.slice(0, 4);
  $("label").innerHTML = `${Y}<span class="sub">연간 계획</span>`;
  $("view").innerHTML = `<div class="loading">불러오는 중…</div>`;
  try { await loadReportList(); if (seq === loadSeq) renderYear(); } catch (e) { if (seq === loadSeq) showError(e); }
}
function renderYear() {
  const Y = +anchor.slice(0, 4), today = todayKST();
  const months = [[Y - 1, 12], ...Array.from({ length: 12 }, (_, k) => [Y, k + 1]), [Y + 1, 1], [Y + 1, 2]];
  const mini = ([y, m]) => {
    const first = `${y}-${pad(m)}-01`, cells = [];
    for (let k = 0; k < wday(first); k++) cells.push("<span></span>");
    for (const s of monthDays(first)) {
      const c = [dateCls(s), s === today ? "today" : "", examOf(s) ? "exam" : "", (school().notes || {})[s] ? "note" : "", reportSet.has(s) ? "rep" : ""].join(" ");
      cells.push(`<button class="${c}" data-act="ygo" data-date="${s}" title="${esc(schoolOff(s) || examOf(s) || (school().notes || {})[s] || "")}">${+s.slice(8)}</button>`);
    }
    return `<div class="mini"><div class="mt">${m === 1 || (y === Y - 1 && m === 12) ? `${y}.${m}` : m}</div>
      <div class="mh">${"SMTWTFS".split("").map((x, k) => `<span class="${k === 0 ? "sun" : k === 6 ? "sat" : ""}">${x}</span>`).join("")}</div>
      <div class="mg">${cells.join("")}</div></div>`;
  };
  $("view").innerHTML = `<section class="day year"><div class="ybig">${Y}</div><div class="ygrid">${months.map(mini).join("")}</div>
    <div class="legend"><span><i class="lg red"></i>쉬는 날</span><span><i class="lg vac"></i>방학</span><span><i class="lg exam"></i>시험</span><span><i class="lg note"></i>학사일정</span><span><i class="lg rep"></i>보고서</span></div>
    <div class="empty">날짜를 누르면 그날 일정이 열려요.</div></section>`;
}

/* ---------- 그리기 ---------- */
function render() {
  if (mode === "year") return renderYear();
  const note = fileExists || mode === "today" ? "" :
    `<div class="note">아직 이 ${mode === "week" ? "주" : "달"}의 표가 없어서 기본 시간표를 보여주고 있어요. ✏️로 고치고 저장하면 표가 만들어져요.</div>`;
  let html = note;
  if (mode === "today") html += dayCard(days.findIndex(d => d.iso === anchor));
  else if (mode === "week") html += gritCard() + days.map((_, i) => dayCard(i)).join("");
  else {
    const m = +anchor.slice(5, 7);
    html += listCard("goal", `🎯 ${m}월의 목표`, "✏️을 눌러 이번 달 목표를 적어 보세요.")
      + monthGrid() + dayCard(days.findIndex(d => d.iso === selDay))
      + listCard("memo", "🗒️ MEMO", "✏️을 눌러 이번 달 메모를 적어 보세요.");
  }
  $("view").innerHTML = html;
}

$("view").addEventListener("change", ev => {
  if (ev.target.id === "rdate" && ev.target.value) { anchor = ev.target.value; load(); }
});
$("view").addEventListener("input", ev => {
  const t = ev.target;
  if (repDraft && t.dataset.r) return reportInput(t);
  if (noteDraft && t.dataset.n) { noteDraft[t.dataset.n] = t.value; return; }
  if (t.id === "rsearch") { allQuery = t.value; return renderAllResults(); }
  if (examDraft && t.dataset.x) return examInput(t);
  if (tbDraft && t.dataset.tb) return tbInput(t);
  if (placeDraft && t.dataset.q) { placeDraft[t.dataset.q] = t.value; return; }
  if (weakDraft && t.dataset.wk) { weakDraft[t.dataset.wk] = t.type === "checkbox" ? t.checked : t.value; return; }
  if (secEdit) {
    if (t.dataset.s === "text") secEdit.draft = t.value;
    else if (t.dataset.s === "must") secEdit.draft.must = t.value;
    else if (t.dataset.g) secEdit.draft.rows[+t.closest(".grow").dataset.k][t.dataset.g] = t.value;
    return;
  }
  if (!editing) return;
  const dr = editing.draft;
  if (t.dataset.t) { dr.tasks[+t.closest(".trow").dataset.k].text = t.value; return; }
  const f = t.dataset.f; if (!f) return;
  const e = dr.events[+t.closest(".ev").dataset.j];
  if (f === "remind") {
    const v = t.value.trim();
    e.remind = v === "" ? null : /^없음|^x$/i.test(v) ? [] : v.split(/[,\s]+/).map(Number).filter(n => Number.isFinite(n) && n >= 0);
  } else e[f] = t.value;
  if (f === "title") t.closest(".ev").querySelector('[data-f="remind"]').placeholder = "기본: " + remindText(defaultRemind(t.value.trim()));
});
$("view").addEventListener("click", async ev => {
  const b = ev.target.closest("button[data-act]"); if (!b || saving) return;
  const act = b.dataset.act;
  if (act.startsWith("r")) return reportClick(b);
  if (act.startsWith("x")) return examClick(b);
  if (act.startsWith("q")) return placeClick(b);
  if (act.startsWith("L")) return learnClick(b);
  if (act.startsWith("w")) return webClick(b);
  if (act.startsWith("K")) return weakClick(b);
  if (act === "ncat") { newsCat = b.dataset.k; store("ncat", newsCat); newsShow = NEWS_PAGE; return renderNews(); }
  if (act === "nmore") { newsShow += NEWS_PAGE; return newsList(); }
  if (act === "ngonotice") { if (!leaveOk()) return; mode = "notice"; store("mode", mode); return load(); }
  if (act === "ngonews") { if (!leaveOk()) return; newsYear = ""; mode = "news"; store("mode", mode); return load(); }
  if (act === "ygo") { mode = "today"; store("mode", mode); anchor = b.dataset.date; return load(); }
  if (act === "pick") { if (!leaveOk()) return; editing = null; selDay = days[+b.dataset.i].iso; render(); return; }
  if (act === "sedit") {
    if (!leaveOk()) return; editing = null;
    const key = b.dataset.key;
    secEdit = key === "grit"
      ? { key, draft: { rows: (r => r.length ? r : GRIT_DEFAULT.map(s => ({ subject: s, content: "", day: "" })))(gritOf(viewText)), must: listOf(viewText, SEC.must).join("\n") } }
      : { key, draft: listOf(viewText, SEC[key]).join("\n") };
    return render();
  }
  if (act === "scancel") { secEdit = null; return render(); }
  if (act === "ssave") return saveSection();
  if (act === "gadd") { secEdit.draft.rows.push({ subject: "", content: "", day: "" }); return render(); }
  if (act === "gdel") { secEdit.draft.rows.splice(+b.closest(".grow").dataset.k, 1); return render(); }
  const i = +b.closest(".day").dataset.i;
  if (act === "chk") {     // ✅ 체크는 바로 저장
    const day = structuredClone(days[i].day), k = +b.dataset.k, m = day.memos[k];
    day.memos[k] = isDone(m) ? taskText(m) : "✅ " + m;
    return saveDay(i, day, true);
  }
  if (act === "edit") {
    if (!leaveOk()) return; secEdit = null;
    const draft = structuredClone(days[i].day);
    draft.tasks = draft.memos.map(m => ({ text: taskText(m), done: isDone(m) }));
    editing = { i, draft };
  } else if (act === "cancel") editing = null;
  else if (act === "save") return saveDay(editing.i, clean(editing.draft));
  else if (act === "add") editing.draft.events.push({ start: "", end: "", title: "", remind: null });
  else if (act === "del") editing.draft.events.splice(+b.closest(".ev").dataset.j, 1);
  else if (act === "tadd") editing.draft.tasks.push({ text: "", done: false });
  else if (act === "tdel") editing.draft.tasks.splice(+b.closest(".trow").dataset.k, 1);
  else if (act === "tchk") { const t = editing.draft.tasks[+b.closest(".trow").dataset.k]; t.done = !t.done; }
  render();
  const card = document.querySelector(".day.editing");
  if (act === "edit" && card) card.scrollIntoView({ block: "nearest", behavior: "smooth" });
  if (act === "add" && card) [...card.querySelectorAll(".ev")].pop()?.querySelector('[data-f="start"]').focus();
  if (act === "tadd" && card) [...card.querySelectorAll(".trow input")].pop()?.focus();
});

/* ---------- 저장 ---------- */
const allRows = (override = {}) => Object.fromEntries(days.map(x => [x.iso, override[x.iso] || formatRow(x.iso, x.day)]));
// 알람은 전날 밤 10시에 다음 날 것을 미리 예약해요
function alarmNote(s) {
  const t = todayKST(), hour = new Date(Date.now() + 9 * 3600e3).getUTCHours();
  if (s < t) return "저장됨 ✓";
  if (s === t || (s === addDays(t, 1) && hour >= 22)) return "저장됨 ✓ 이 날 알람은 이미 예약돼서 앱에만 반영돼요";
  return "저장됨 ✓ 전날 밤 10시에 알람이 예약될 때 반영돼요";
}
async function saveDay(i, day, quick) {
  const d = days[i], row = formatRow(d.iso, day);
  if (fileExists && row === formatRow(d.iso, d.day)) { editing = null; render(); return; }
  saving = true; if (!quick) render();
  try {
    const msg = `앱에서 ${mmdd(d.iso)} 계획 ${quick ? "체크" : "수정"}`;
    await updateFile(viewPath(), text => text ? replaceRows(text, viewRef(), { [d.iso]: row }) : newTable(viewTitle(), viewDays(), allRows({ [d.iso]: row })), msg);
    // 반대쪽 표(주간↔월간)가 이미 있으면 그 날짜도 같이 고쳐서 항상 같은 내용 유지
    const other = weekish() ? monthPath(d.iso) : weekPath(d.iso);
    const ref = weekish() ? monthFirst(d.iso) : weekStart(d.iso);
    if (await getFile(other, true)) await updateFile(other, text => replaceRows(text, ref, { [d.iso]: row }), msg);
    fileExists = true; viewText = files.get(viewPath()).text; d.day = day; editing = null;
    if (!quick) toast(alarmNote(d.iso), 3500);
  } catch (e) { saving = false; render(); showError(e, true); return; }
  saving = false; render();
}
async function saveSection() {
  const { key, draft } = secEdit;
  const lines = t => t.split("\n").map(x => x.trim().replace(/^[-*]\s*/, "")).filter(Boolean).map(x => "- " + x.replace(/^#/, "＃"));
  const cell = t => (t || "").replace(/\|/g, "/").trim();
  saving = true; render();
  try {
    await updateFile(viewPath(), text => {
      let t = text || newTable(viewTitle(), viewDays(), allRows());
      if (key === "grit") {
        const rows = draft.rows.filter(r => r.subject.trim() || r.content.trim());
        t = setSection(t, SEC.grit, rows.length ? ["| 과목 | 내용 | 요일 |", "|---|---|---|", ...rows.map(r => `| ${cell(r.subject)} | ${cell(r.content)} | ${cell(r.day)} |`)] : []);
        t = setSection(t, SEC.must, lines(draft.must));
      } else t = setSection(t, SEC[key], lines(draft));
      return t;
    }, `앱에서 ${key === "grit" ? "주간 GRIT" : key === "goal" ? "이달의 목표" : "월간 MEMO"} 수정`);
    fileExists = true; viewText = files.get(viewPath()).text; secEdit = null;
    toast("저장됨 ✓");
  } catch (e) { saving = false; render(); showError(e, true); return; }
  saving = false; render();
}

function errorText(e, writing) {
  const msg = e.message || String(e);
  if (SB && (e.status === 401 || e.status === 403)) return "로그인이 풀렸어요. ⚙️ 에서 다시 로그인해 주세요.";
  if (e.status === 401) return "토큰이 틀렸거나 만료됐어요. ⚙️ 설정에서 토큰을 다시 넣어 주세요.";
  if (writing && (e.status === 403 || e.status === 404))
    return "저장 권한이 없어요 (" + e.status + ").\n토큰 설정에서 확인하세요:\n① Repository access → Only select repositories → alam 선택\n② Permissions → Repositories → Contents: Read and write";
  if (e.status === 403) return "권한이 없어요. 토큰 설정을 확인하세요.\n" + msg;
  return msg;
}
function showError(e, writing) {
  console.error(e);
  const text = errorText(e, writing);
  document.querySelectorAll(".panel.error").forEach(x => x.remove());
  const html = `<div class="panel error"><div class="err">⚠️ ${esc(text)}</div>
    ${writing && !SB ? '<p style="margin:8px 0 0"><a href="https://github.com/settings/personal-access-tokens" target="_blank" rel="noopener">내 토큰 설정 열기 →</a></p>' : ""}</div>`;
  const card = document.querySelector(".day.editing");
  if (card) { card.insertAdjacentHTML("beforeend", html); card.scrollIntoView({ block: "end", behavior: "smooth" }); }
  else { $("view").insertAdjacentHTML("afterbegin", html); window.scrollTo({ top: 0, behavior: "smooth" }); }
  toast("⚠️ 저장 실패", 3000);
}

/* ---------- 수업 보고서 ---------- */
// plans/report/YYYY-MM-DD.md  (마크다운이라 GitHub에서도 읽기 쉬움)
const reportPath = s => `plans/report/${s}.md`;
const SUBJECTS = ["국어", "수학", "영어", "한국사", "통합사회", "통합과학", "물리", "화학", "생명과학", "지구과학", "사회", "역사", "정보", "체육", "음악", "미술", "기술가정", "한문", "제2외국어", "진로", "창체"];
const RSECS = [
  ["important", "⭐ 중요한 것", "선생님이 강조한 것, 시험에 나온다고 한 것"],
  ["memorize", "🧠 외워야 할 것", "단어, 공식, 연도 등 (다음 날 자정 알림에 같이 와요)"],
  ["remember", "📌 기억해야 할 것", "숙제, 준비물, 수행평가·시험 날짜 (다음 날 자정 알림에 같이 와요)"],
  ["etc", "✍️ 기타 메모", "오늘 느낀 점, 질문할 것 등"],
];
let reportSet = new Set();   // 보고서가 있는 날짜들
let rep = { exists: false, data: null };
let repDraft = null;

const emptyReport = () => ({ classes: [], important: "", memorize: "", remember: "", etc: "" });
function parseReport(text) {
  const r = emptyReport(); if (!text) return r;
  const buf = { important: [], memorize: [], remember: [], etc: [] };
  let sec = null, cur = null;
  for (const line of text.split("\n")) {
    if (line.startsWith("## ")) {
      sec = /수업/.test(line) ? "classes" : /중요/.test(line) ? "important" : /외워/.test(line) ? "memorize" : /기억/.test(line) ? "remember" : "etc";
      cur = null; continue;
    }
    if (line.startsWith("# ") || line.startsWith("> ")) continue;
    if (sec === "classes") {
      if (line.startsWith("### ")) { cur = { subject: line.slice(4).trim(), text: [] }; r.classes.push(cur); }
      else if (cur) cur.text.push(line);
    } else if (sec) buf[sec].push(line);
  }
  r.classes.forEach(c => c.text = c.text.join("\n").trim());
  for (const k in buf) r[k] = buf[k].map(l => l.replace(/^\s*[-*]\s?/, "")).join("\n").trim();
  return r;
}
const safeLine = l => l.replace(/^#/, "＃");
function buildReport(s, r) {
  if (!r) return "";
  const out = [`# ${s.replace(/-/g, ".")} (${WD[wday(s)]}) 수업 보고서`, "", "## 📚 수업 내용", ""];
  for (const c of r.classes) {
    const subj = (c.subject || "").trim(), text = (c.text || "").trim();
    if (!text) continue;   // 내용 없는 과목은 저장 안 함
    out.push(`### ${subj || "기타"}`, ...text.split("\n").map(safeLine), "");
  }
  for (const [k, title] of RSECS) {
    out.push(`## ${title}`, "");
    const lines = (r[k] || "").split("\n").map(l => l.trim()).filter(Boolean);
    out.push(...lines.map(l => "- " + safeLine(l.replace(/^[-*]\s?/, ""))), "");
  }
  return out.join("\n").replace(/\n{3,}/g, "\n\n").trimEnd() + "\n";
}
async function loadReportList() {
  try {
    reportSet = new Set((await listDir("plans/report")).map(n => n.replace(/\.md$/, "")));
  } catch (e) { reportSet = new Set(); }
}
async function loadReport(seq = loadSeq) {
  renderKindBar();
  if (reportKind === "free") return loadNotes(seq);
  if (reportKind === "all") return loadAll(seq);
  const w = wday(anchor);
  $("label").innerHTML = `${mmdd(anchor)} (${WD[w]})<span class="sub">${anchor.slice(0, 4)}년 수업 보고서</span>`;
  $("view").innerHTML = `<div class="loading">불러오는 중…</div>`;
  try {
    const f = await getFile(reportPath(anchor), true);
    await loadReportList();
    if (seq !== loadSeq) return;
    rep = { exists: !!f, data: parseReport(f && f.text) };
    renderReport();
  } catch (e) { if (seq === loadSeq) showError(e); }
}
const bullets = t => `<ul>${t.split("\n").filter(Boolean).map(l => `<li>${esc(l)}</li>`).join("")}</ul>`;
function renderReport() {
  const today = todayKST(), w = wday(anchor), ed = !!repDraft;
  const head = `<div class="dhead"><span class="date ${w === 0 ? "sun" : w === 6 ? "sat" : ""}">${mmdd(anchor)} (${WD[w]})</span>
    ${anchor === today ? '<span class="badge">오늘</span>' : ""}<span class="sp"></span>
    ${ed ? "" : `<button class="pencil" data-act="redit" aria-label="보고서 ${rep.exists ? "수정" : "쓰기"}" title="수정">✏️</button>`}</div>`;
  const ttSubj = Object.values(school().timetable || {}).flat();
  const dl = `<datalist id="subjects">${[...new Set([...ttSubj, ...SUBJECTS])].map(x => `<option value="${x}">`).join("")}</datalist>`;
  if (!ed) {
    const r = rep.data;
    let body = "";
    if (!rep.exists) body = `<div class="empty">아직 보고서가 없어요. ✏️을 눌러 ${anchor === today ? "오늘" : "이날"} 한 것을 정리해 보세요. 지난 날짜도 쓸 수 있어요.</div>`;
    else {
      body += `<div class="rsec"><h3>📚 수업 내용</h3>${r.classes.length ? r.classes.map(c => `<div class="subj"><b>${esc(c.subject)}</b><div class="pre">${esc(c.text)}</div></div>`).join("") : '<div class="empty">-</div>'}</div>`;
      for (const [k, title] of RSECS) if (r[k]) body += `<div class="rsec"><h3>${title}</h3>${bullets(r[k])}</div>`;
    }
    const past = [...reportSet].sort().reverse().filter(x => x !== anchor).slice(0, 30);
    $("view").innerHTML = kindBar() + `<div class="datepick">📅 <input type="date" id="rdate" value="${anchor}" max="${addDays(today, 1)}" aria-label="날짜 고르기">
        ${anchor !== today ? '<button class="btn ghost" data-act="rtoday">오늘</button>' : ""}</div>
      <section class="day">${head}${body}</section>
      <section class="day"><div class="dhead"><span class="date">📚 지난 보고서</span></div>
        ${past.length ? `<div class="pastlist">${past.map(x => `<button data-act="rgo" data-date="${x}">${mmdd(x)} (${WD[wday(x)]})</button>`).join("")}</div>`
          : '<div class="empty">아직 없어요. 위 📅에서 지난 날짜를 골라 쓸 수 있어요.</div>'}</section>`;
    return;
  }
  const d = repDraft;
  $("view").innerHTML = kindBar() + `<section class="day editing rform">${head}${dl}
    <label>📚 수업 내용 <span class="hint">— 과목별로 오늘 배운 것 (안 쓴 과목은 저장 안 돼요)</span></label>
    ${d.classes.map((c, j) => `<div class="sedit" data-j="${j}">
      <input data-r="subject" list="subjects" value="${esc(c.subject)}" placeholder="과목 (예: 수학)">
      <button class="del" data-act="rdel" aria-label="과목 삭제">×</button>
      <textarea data-r="text" placeholder="오늘 배운 내용 (단원, 핵심 개념, 예제 등)">${esc(c.text)}</textarea></div>`).join("")}
    <button class="add" data-act="radd" style="width:100%">+ 과목 추가</button>
    ${RSECS.map(([k, title, hint]) => `<label>${title} <span class="hint">— ${hint}</span></label>
      <textarea data-r="${k}" placeholder="한 줄에 하나씩">${esc(d[k])}</textarea>`).join("")}
    <div class="actions" style="margin-top:12px">
      <button class="btn ghost" data-act="rcancel" ${saving ? "disabled" : ""}>취소</button>
      <button class="btn" data-act="rsave" ${saving ? "disabled" : ""}>${saving ? "저장 중…" : "저장"}</button>
    </div></section>`;
}
function reportInput(t) {
  const k = t.dataset.r;
  if (k === "subject" || k === "text") repDraft.classes[+t.closest(".sedit").dataset.j][k] = t.value;
  else repDraft[k] = t.value;
}
async function reportClick(b) {
  const act = b.dataset.act;
  if (act === "report") {            // 주간/월간 카드의 📒 버튼
    if (!leaveOk()) return;
    anchor = days[+b.closest(".day").dataset.i].iso; mode = "report"; store("mode", mode);
    reportKind = "date"; store("rkind", "date"); return load();
  }
  if (act === "rfilter") { allSubj = b.dataset.s; return renderAll(); }
  if (act === "ropen") {
    if (b.dataset.kind === "date") { reportKind = "date"; anchor = b.dataset.key; }
    else { reportKind = "free"; noteOpen = b.dataset.key; }
    store("rkind", reportKind); return load();
  }
  if (act === "rkind") { if (!leaveOk()) return; reportKind = b.dataset.kind; store("rkind", reportKind); noteOpen = null; noteDraft = null; return load(); }
  if (act.startsWith("rn")) return noteClick(b);
  if (act === "rgo" || act === "rtoday") { anchor = act === "rgo" ? b.dataset.date : todayKST(); return load(); }
  if (act === "redit") {
    const draft = structuredClone(rep.data);
    if (!draft.classes.length) {
      // 그날 시간표 과목 + 학원 등 일정으로 미리 채움 (내용을 안 쓴 칸은 저장 안 됨)
      const st = new Set(school().school_events || []);
      const subj = [...new Set([
        ...classesOf(anchor).filter(c => !/창체|동아리|진로/.test(c)),
        ...(await resolveDay(anchor)).events.map(e => e.title).filter(t => !st.has(t)),
      ])];
      draft.classes = subj.length ? subj.map(x => ({ subject: x, text: "" })) : [{ subject: "", text: "" }];
    }
    repDraft = draft;
  } else if (act === "rcancel") repDraft = null;
  else if (act === "radd") repDraft.classes.push({ subject: "", text: "" });
  else if (act === "rdel") repDraft.classes.splice(+b.closest(".sedit").dataset.j, 1);
  else if (act === "rsave") return saveReport();
  renderReport();
  if (act === "radd") [...document.querySelectorAll(".sedit input")].pop()?.focus();
}
async function saveReport() {
  const text = buildReport(anchor, repDraft);
  if (rep.exists && text === buildReport(anchor, rep.data)) { repDraft = null; return renderReport(); }
  saving = true; renderReport();
  try {
    await updateFile(reportPath(anchor), () => text, `앱에서 ${mmdd(anchor)} 보고서 ${rep.exists ? "수정" : "작성"}`);
    rep = { exists: true, data: parseReport(text) }; reportSet.add(anchor); repDraft = null;
    toast("보고서 저장됨 ✓", 2500);
  } catch (e) { saving = false; renderReport(); showError(e, true); return; }
  saving = false; renderReport();
}


/* ---------- 자유 보고서 (날짜 없이 쓰는 보고서) ---------- */
// plans/notes/<만든 시각>.md  — 파일 이름은 구분용일 뿐, 날짜와 상관없이 언제든 써요
let reportKind = ["free", "all"].includes(store("rkind")) ? store("rkind") : "date";
let notes = [];          // [{id, path, data}]
let noteOpen = null;     // 열어 본 보고서 id
let noteDraft = null;    // 수정 중 (새 보고서면 id 없음)
const NSECS = RSECS;     // 중요한 것 / 외워야 할 것 / 기억해야 할 것 / 기타
const kindBar = () => `<div class="kindbar">
  <button data-act="rkind" data-kind="date" class="${reportKind === "date" ? "on" : ""}">📅 날짜별</button>
  <button data-act="rkind" data-kind="free" class="${reportKind === "free" ? "on" : ""}">📝 자유</button>
  <button data-act="rkind" data-kind="all" class="${reportKind === "all" ? "on" : ""}">📚 모아보기</button></div>`;
function renderKindBar() {}
const emptyNote = () => ({ title: "", subject: "", body: "", important: "", memorize: "", remember: "", etc: "" });
function parseNote(text) {
  const n = emptyNote(); if (!text) return n;
  const buf = { body: [], important: [], memorize: [], remember: [], etc: [] };
  let sec = null;
  for (const line of text.split("\n")) {
    if (line.startsWith("# ") && !n.title) { n.title = line.slice(2).trim(); continue; }
    const sm = line.match(/^>\s*과목:\s*(.*)$/); if (sm && !sec) { n.subject = sm[1].trim(); continue; }
    if (line.startsWith("## ")) {
      sec = /내용/.test(line) ? "body" : /중요/.test(line) ? "important" : /외워/.test(line) ? "memorize" : /기억/.test(line) ? "remember" : "etc";
      continue;
    }
    if (sec) buf[sec].push(line);
  }
  n.body = buf.body.join("\n").trim();
  for (const k of ["important", "memorize", "remember", "etc"]) n[k] = buf[k].map(l => l.replace(/^\s*[-*]\s?/, "")).join("\n").trim();
  return n;
}
function buildNote(n) {
  const out = [`# ${(n.title || "").trim() || "제목 없음"}`, ""];
  if ((n.subject || "").trim()) out.push(`> 과목: ${n.subject.trim()}`, "");
  out.push("## 📚 내용", "", ...(n.body || "").trim().split("\n").map(safeLine), "");
  for (const [k, title] of NSECS) {
    out.push(`## ${title}`, "");
    out.push(...(n[k] || "").split("\n").map(l => l.trim()).filter(Boolean).map(l => "- " + safeLine(l.replace(/^[-*]\s?/, ""))), "");
  }
  return out.join("\n").replace(/\n{3,}/g, "\n\n").trimEnd() + "\n";
}
function noteId() {   // 만든 시각(밀리초까지) + 겹치지 않게 확인
  const d = new Date(Date.now() + 9 * 3600e3).toISOString();
  let id = d.slice(0, 10).replace(/-/g, "") + "-" + d.slice(11, 23).replace(/[:.]/g, "");
  while (notes.some(n => n.id === id)) id += Math.floor(Math.random() * 10);
  return id;
}
async function loadNotes(seq = loadSeq) {
  $("label").innerHTML = `자유 보고서<span class="sub">날짜 없이 언제든 정리</span>`;
  $("view").innerHTML = kindBar() + `<div class="loading">불러오는 중…</div>`;
  try {
    const names = (await listDir("plans/notes")).filter(n => n.endsWith(".md")).sort().reverse();
    const out = [];
    for (const name of names) {
      const path = `plans/notes/${name}`, f = await getFile(path);
      if (f) out.push({ id: name.replace(/\.md$/, ""), path, data: parseNote(f.text) });
    }
    if (seq !== loadSeq) return;
    notes = out; renderNotes();
  } catch (e) { if (seq === loadSeq) showError(e); }
}
function noteForm(d) {
  const ttSubj = Object.values(school().timetable || {}).flat();
  return `<section class="day editing rform">
    <div class="dhead"><span class="date">${d.id ? "✏️ 보고서 수정" : "📝 새 보고서"}</span></div>
    <datalist id="subjects">${[...new Set([...ttSubj, ...SUBJECTS])].map(x => `<option value="${x}">`).join("")}</datalist>
    <label>제목</label><input data-n="title" value="${esc(d.title)}" placeholder="예) 이차함수 정리, 임진왜란 흐름">
    <label>과목 <span class="hint">— 선택</span></label><input data-n="subject" list="subjects" value="${esc(d.subject)}" placeholder="예) 수학">
    <label>📚 내용 <span class="hint">— 배운 것, 정리한 것</span></label>
    <textarea data-n="body" style="min-height:140px" placeholder="자유롭게 적어요">${esc(d.body)}</textarea>
    ${NSECS.map(([k, title]) => `<label>${title}</label><textarea data-n="${k}" placeholder="한 줄에 하나씩">${esc(d[k])}</textarea>`).join("")}
    <div class="actions" style="margin-top:12px">
      ${d.id ? `<button class="btn ghost danger" data-act="rndel" ${saving ? "disabled" : ""} style="margin-right:auto">🗑 삭제</button>` : ""}
      <button class="btn ghost" data-act="rncancel" ${saving ? "disabled" : ""}>취소</button>
      <button class="btn" data-act="rnsave" ${saving ? "disabled" : ""}>${saving ? "저장 중…" : "저장"}</button>
    </div></section>`;
}
function renderNotes() {
  let html = kindBar();
  if (noteDraft) html += noteForm(noteDraft);
  else if (noteOpen) {
    const n = notes.find(x => x.id === noteOpen);
    if (!n) { noteOpen = null; return renderNotes(); }
    const d = n.data;
    html += `<button class="btn ghost" data-act="rnback" style="margin-bottom:10px">‹ 목록</button>
      <section class="day"><div class="dhead"><span class="date">${esc(d.title || "제목 없음")}</span>
        ${d.subject ? `<span class="chip">${esc(d.subject)}</span>` : ""}<span class="sp"></span>
        <button class="pencil" data-act="rnedit" aria-label="수정">✏️</button></div>
        ${d.body ? `<div class="rsec"><h3>📚 내용</h3><div class="pre">${esc(d.body)}</div></div>` : ""}
        ${NSECS.map(([k, title]) => d[k] ? `<div class="rsec"><h3>${title}</h3>${bullets(d[k])}</div>` : "").join("")}
      </section>`;
  } else {
    html += `<button class="add" data-act="rnnew" style="width:100%;margin-bottom:10px;background:var(--card)">+ 새 자유 보고서</button>`;
    html += notes.length ? notes.map(n => {
      const preview = (n.data.body || n.data.important || n.data.memorize || "").split("\n")[0];
      return `<button class="day notecard" data-act="rnopen" data-id="${n.id}">
        <div class="dhead"><span class="date">${esc(n.data.title || "제목 없음")}</span>${n.data.subject ? `<span class="chip">${esc(n.data.subject)}</span>` : ""}</div>
        ${preview ? `<div class="empty">${esc(preview)}</div>` : ""}</button>`;
    }).join("") : `<div class="day"><div class="empty">아직 없어요. 날짜가 기억나지 않는 내용, 단원 정리, 시험 대비 요약 등을 자유롭게 적어 보세요.</div></div>`;
  }
  $("view").innerHTML = html;
}
async function noteClick(b) {
  const act = b.dataset.act;
  if (act === "rnnew") noteDraft = emptyNote();
  else if (act === "rnopen") noteOpen = b.dataset.id;
  else if (act === "rnback") noteOpen = null;
  else if (act === "rnedit") { const n = notes.find(x => x.id === noteOpen); noteDraft = { ...structuredClone(n.data), id: n.id }; }
  else if (act === "rncancel") noteDraft = null;
  else if (act === "rnsave") return saveNote();
  else if (act === "rndel") return deleteNote();
  renderNotes();
  if (act === "rnnew") document.querySelector('[data-n="title"]')?.focus();
  window.scrollTo({ top: 0 });
}
async function saveNote() {
  const d = noteDraft;
  if (!(d.title || "").trim() && !(d.body || "").trim()) { toast("제목이나 내용을 적어 주세요"); return; }
  const id = d.id || noteId(), path = `plans/notes/${id}.md`, text = buildNote(d);
  saving = true; renderNotes();
  try {
    await updateFile(path, () => text, `앱에서 자유 보고서 ${d.id ? "수정" : "작성"}: ${(d.title || "").trim() || "제목 없음"}`);
    const item = { id, path, data: parseNote(text) };
    notes = [item, ...notes.filter(x => x.id !== id)].sort((a, b) => b.id.localeCompare(a.id));
    noteDraft = null; noteOpen = id; toast("보고서 저장됨 ✓");
  } catch (e) { saving = false; renderNotes(); showError(e, true); return; }
  saving = false; renderNotes();
}
async function deleteNote() {
  const d = noteDraft;
  if (!confirm(`'${d.title || "제목 없음"}' 보고서를 지울까요? 되돌릴 수 없어요.`)) return;
  const path = `plans/notes/${d.id}.md`;
  saving = true; renderNotes();
  try {
    const f = await getFile(path, true);
    if (f) await deleteFile(path, `앱에서 자유 보고서 삭제: ${d.title || "제목 없음"}`);
    files.delete(path); notes = notes.filter(x => x.id !== d.id); noteDraft = null; noteOpen = null; toast("지웠어요");
  } catch (e) { saving = false; renderNotes(); showError(e, true); return; }
  saving = false; renderNotes();
}


/* ---------- 과목 묶음 (공수2·수학 → 수학 등) ---------- */
const SUBJECT_GROUPS = [
  ["국어", /^(국어|공국|공통국어|문학|독서|화법과작문|언어와매체)\d*$/, /국어|공국|문학|독서/],
  ["수학", /^(수학|공수|공통수학|미적분|확률과통계|기하)\d*$/, /수학|공수|미적|확통|기하/],
  ["영어", /^(영어|공영|공통영어|영어회화|영어독해)\d*$/, /영어|공영|영단어/],
  ["한국사", /^(한국사|국사)\d*$/, /한국사|국사/],
  ["사회", /^(사회|통사|통합사회|사탐|사회탐구)\d*$/, /사회|통사|사탐/],
  ["과학", /^(과학|통과|통합과학|과탐|과학탐구실험|물리|화학|생명과학|지구과학|생물|지구)\d*$/, /과학|통과|과탐|물리|화학|생명|지구과학/],
];
function subjectGroup(name) {
  const n = String(name || "").replace(/\s+/g, "").replace(/[ⅠⅡ]/g, m => m === "Ⅰ" ? "1" : "2");
  for (const [g, re] of SUBJECT_GROUPS) if (re.test(n)) return g;
  return String(name || "").trim();
}
function guessSubject(text) {   // 자유 글에서 과목 짐작 (한국사를 국어보다 먼저)
  const order = ["한국사", "국어", "수학", "영어", "사회", "과학"];
  text = String(text).replace(/인사탐|인문사회/g, "");   // 방과후 '인사탐'은 사회 과목이 아님
  for (const g of order) { const e = SUBJECT_GROUPS.find(x => x[0] === g); if (e[2].test(text)) return g; }
  return "";
}

/* ---------- 보고서 모아보기 ---------- */
let allItems = [];       // [{kind:'date'|'free', key, title, subjects:[], blocks:[{subject,text}], lists:{...}}]
let allQuery = "", allSubj = "";
async function loadAll(seq = loadSeq) {
  $("label").innerHTML = `보고서 모아보기<span class="sub">날짜별 + 자유 보고서 전부</span>`;
  $("view").innerHTML = kindBar() + `<div class="loading">불러오는 중…</div>`;
  try {
    await loadReportList();
    const out = [];
    for (const dte of [...reportSet].sort().reverse()) {
      const f = await getFile(reportPath(dte)); if (!f) continue;
      const r = parseReport(f.text);
      out.push({ kind: "date", key: dte, title: `${dte.replace(/-/g, ".")} (${WD[wday(dte)]})`, blocks: r.classes, lists: r });
    }
    for (const name of (await listDir("plans/notes")).filter(n => n.endsWith(".md"))) {
      const f = await getFile(`plans/notes/${name}`); if (!f) continue;
      const n = parseNote(f.text);
      out.push({ kind: "free", key: name.replace(/\.md$/, ""), title: n.title || "제목 없음", blocks: n.body ? [{ subject: n.subject || "📝 자유", text: n.body }] : [], lists: n });
    }
    if (seq !== loadSeq) return;
    allItems = out; renderAll();
  } catch (e) { if (seq === loadSeq) showError(e); }
}
function renderAll() {
  const ORDER = SUBJECT_GROUPS.map(g => g[0]);
  const subj = [...new Set(allItems.flatMap(x => x.blocks.map(b => subjectGroup(b.subject))).filter(Boolean))]
    .sort((a, b) => (ORDER.indexOf(a) + 1 || 99) - (ORDER.indexOf(b) + 1 || 99));
  $("view").innerHTML = kindBar() +
    `<input class="search" id="rsearch" value="${esc(allQuery)}" placeholder="🔍 검색 (예: 함수, 해류)">
     <div class="filters"><button data-act="rfilter" data-s="" class="${allSubj ? "" : "on"}">전체</button>
       ${subj.map(x => `<button data-act="rfilter" data-s="${esc(x)}" class="${allSubj === x ? "on" : ""}">${esc(x)}</button>`).join("")}</div>
     <div id="allres"></div>`;
  renderAllResults();
}
function renderAllResults() {
  const q = allQuery.trim().toLowerCase();
  const hl = t => { const e = esc(t); if (!q) return e; const i = e.toLowerCase().indexOf(esc(q)); return i < 0 ? e : e.slice(0, i) + `<mark class="hl">${e.slice(i, i + esc(q).length)}</mark>` + e.slice(i + esc(q).length); };
  const match = t => !q || (t || "").toLowerCase().includes(q);
  const cards = allItems.map(it => {
    const blocks = it.blocks.filter(b => (!allSubj || subjectGroup(b.subject) === allSubj));
    const lists = allSubj ? [] : RSECS.filter(([k]) => it.lists[k]).map(([k, title]) => [title, it.lists[k]]);
    const text = it.title + " " + blocks.map(b => b.subject + " " + b.text).join(" ") + " " + lists.map(l => l[1]).join(" ");
    if ((allSubj && !blocks.length) || !match(text)) return "";
    return `<section class="day allday">
      <div class="dhead"><h4>${it.kind === "date" ? "📅 " : "📝 "}${hl(it.title)}</h4><span class="sp"></span>
        <button class="mini-btn" data-act="ropen" data-kind="${it.kind}" data-key="${it.key}">열기</button></div>
      ${blocks.map(b => `<div class="subj"><b>${hl(b.subject)}</b><div class="pre">${hl(b.text)}</div></div>`).join("")}
      ${lists.map(([title, t]) => `<div class="rsec"><h3>${title}</h3><ul>${t.split("\n").filter(Boolean).map(l => `<li>${hl(l)}</li>`).join("")}</ul></div>`).join("")}
    </section>`;
  }).filter(Boolean);
  $("allres").innerHTML = cards.length ? cards.join("") : `<div class="day"><div class="empty">${allItems.length ? "찾는 내용이 없어요." : "아직 쓴 보고서가 없어요."}</div></div>`;
}

/* ---------- 시험 범위·진도 (plans/exams.json) ---------- */
const EXAM_PATH = "plans/exams.json";
let examData = { exams: [] }, examDraft = null, examFilter = "all", examOpenPast = false, examCands = null, tbDraft = null;
// 교과서 출판사 (exams.json 의 grade = 지금 학년, textbooks = { 학년: [{subject, publisher}] }). 중1~고3
const GRADES = ["중1", "중2", "중3", "고1", "고2", "고3"];
// 학년별로 먼저 채워 줄 과목 (2·3학년 고등은 선택과목이 학교마다 달라 기본만)
const TB_BASE = {
  중: ["국어", "수학", "영어", "과학", "사회", "역사", "도덕", "기술·가정", "정보", "한문"],
  고1: ["국어", "수학", "영어", "한국사", "사회", "과학", "한문"],
  고: ["국어", "수학", "영어"],
};
const tbBase = g => g.startsWith("중") ? TB_BASE.중 : g === "고1" ? TB_BASE.고1 : TB_BASE.고;
const TB_SUBJ = {   // 과목 입력칸 추천 목록
  중: ["국어", "수학", "영어", "과학", "사회", "역사", "도덕", "기술·가정", "정보", "한문", "체육", "음악", "미술", "생활 일본어", "생활 중국어"],
  고: ["국어", "수학", "영어", "한국사", "사회", "과학", "통합사회", "통합과학", "공통국어", "공통수학", "공통영어", "한문",
    "문학", "독서", "화법과 작문", "언어와 매체", "화법과 언어", "독서와 작문", "수학Ⅰ", "수학Ⅱ", "대수", "미적분", "미적분Ⅰ", "미적분Ⅱ", "확률과 통계", "기하",
    "영어Ⅰ", "영어Ⅱ", "영어 독해와 작문", "영어 회화", "물리학", "화학", "생명과학", "지구과학", "물리학Ⅰ", "화학Ⅰ", "생명과학Ⅰ", "지구과학Ⅰ",
    "물리학Ⅱ", "화학Ⅱ", "생명과학Ⅱ", "지구과학Ⅱ", "한국지리", "세계지리", "세계시민과 지리", "동아시아사", "세계사", "생활과 윤리", "윤리와 사상",
    "현대사회와 윤리", "정치와 법", "정치", "법과 사회", "경제", "사회·문화", "사회와 문화", "정보", "한문Ⅰ", "일본어Ⅰ", "중국어Ⅰ", "일본어", "중국어"],
};
function normGrade(g) {
  g = String(g || "").replace(/\s+/g, "");
  if (GRADES.includes(g)) return g;
  const m = g.match(/(중|고)?[^\d]*([1-3])/);
  return m ? (m[1] || "고") + m[2] : "";
}
function savedTb(data) {   // 저장된 출판사 { grade, textbooks: {학년: [...]} } 또는 null (예전 형식: textbooks 가 배열)
  const t = data.textbooks;
  const school = data.school || "", sch = { name: school, id: data.schoolId || "", addr: data.schoolAddr || "", road: data.schoolRoad || "" };
  if (Array.isArray(t)) { const g = normGrade(data.grade) || "고1"; return { school, sch, grade: g, textbooks: { [g]: t } }; }
  if (t && typeof t === "object") return { school, sch, grade: normGrade(data.grade) || "", textbooks: t };
  return school ? { school, sch, grade: "", textbooks: {} } : null;
}
const tbInfo = () => savedTb(examData) || { school: "", sch: { name: "" }, grade: "", textbooks: {} };
const sharedKey = sch => sch && sch.id ? sch.id : schoolKey(sch && sch.name);   // 학교 목록에서 고른 학교는 학교 id 로 (이름 겹침 방지)
/* 전국 중·고등학교 목록 (docs/schools.json, GitHub Actions 가 한 달에 한 번 공공데이터에서 모음) */
let SCHOOLS = null;
const schoolShort = n => n.replace(/여자고등학교$/, "여고").replace(/남자고등학교$/, "남고").replace(/고등학교$/, "고").replace(/여자중학교$/, "여중").replace(/남자중학교$/, "남중").replace(/중학교$/, "중");
const sidoShort = x => ({ 경상남도: "경남", 경상북도: "경북", 충청남도: "충남", 충청북도: "충북", 전라남도: "전남", 전라북도: "전북", 전북특별자치도: "전북", 강원특별자치도: "강원", 강원도: "강원", 제주특별자치도: "제주", 세종특별자치시: "세종" })[x] || "";
async function loadSchools() {
  if (SCHOOLS) return SCHOOLS.length ? SCHOOLS : null;
  try {
    const r = await fetch("schools.json", { cache: "no-cache" }); if (!r.ok) throw 0;
    const d = await r.json(), F = d.fields;
    SCHOOLS = d.schools.map(a => { const o = Object.fromEntries(F.map((f, i) => [f, a[i]]));
      o.hay = (schoolKey(o.name) + " " + schoolShort(schoolKey(o.name)) + " " + schoolKey(o.jibun) + " " + schoolKey(o.road) + " " + o.sido + " " + sidoShort(o.sido)).toLowerCase(); return o; });
    SCHOOLS.updated = d.updated;
  } catch (e) { SCHOOLS = []; }
  return SCHOOLS.length ? SCHOOLS : null;
}
function searchSchools(list, q, kind) {
  const toks = String(q || "").toLowerCase().split(/\s+/).filter(Boolean).map(t => t.replace(/특별시|광역시|특별자치시|특별자치도/g, ""));
  if (!toks.length || toks.join("").length < 2) return [];
  const first = toks[0];
  return list.filter(o => (!kind || o.kind === kind) && toks.every(t => o.hay.includes(t)))
    .map(o => ({ o, r: schoolKey(o.name).toLowerCase().startsWith(first) || schoolShort(schoolKey(o.name)).toLowerCase() === first ? 0 : 1 }))
    .sort((a, b) => a.r - b.r || a.o.name.localeCompare(b.o.name, "ko") || (a.o.jibun || a.o.road).localeCompare(b.o.jibun || b.o.road, "ko")).map(x => x.o);
}
const mapLink = o => o.lat && o.lng ? `https://map.kakao.com/link/map/${encodeURIComponent(o.name)},${o.lat},${o.lng}` : `https://map.kakao.com/link/search/${encodeURIComponent((o.road || o.jibun || "") + " " + o.name)}`;
const schoolKey = x => String(x || "").replace(/\s+/g, "");
const cleanTb = list => (list || []).map(t => ({ subject: String(t.subject || "").trim(), publisher: String(t.publisher || "").trim() })).filter(t => t.subject || t.publisher);
const sameTb = (a, b) => JSON.stringify(cleanTb(a)) === JSON.stringify(cleanTb(b));
// 학교 공유 (Supabase school_textbooks 표). 표가 아직 없으면 null
async function sharedChoices(sch, grade) {
  if (!SB || !sbUser) return null;
  const { data, error } = await SB.rpc("school_textbook_choices", { p_school: sharedKey(sch), p_grade: grade });
  if (error) { console.warn("공유 출판사", error.message); return null; }
  return (data || []).map(r => ({ list: cleanTb(r.textbooks), people: r.people })).filter(r => r.list.length);
}
async function sharedSchools(q) {
  if (!SB || !sbUser || schoolKey(q).length < 2) return [];
  const { data, error } = await SB.rpc("school_names", { p_q: q });
  return error ? [] : data || [];
}
async function pushShared(sch, grade, list) {   // 내 지금 학년 출판사를 학교 공유 목록에 올림
  const school = sharedKey(sch);
  if (!SB || !sbUser || !school || !GRADES.includes(grade)) return;
  // 다른 사람에게 보이는 값이라 DB 규칙(schema.sql)에 맞춰: 글자 60자까지, <> 빼기
  const shareTxt = s => s.replace(/[<>]/g, "").slice(0, 60);
  list = cleanTb(list).map(t => ({ subject: shareTxt(t.subject), publisher: shareTxt(t.publisher) })).filter(t => t.subject || t.publisher);
  const q = SB.from("school_textbooks");
  const { error } = list.length
    ? await q.upsert({ user_id: sbUser.id, grade, school: school.slice(0, 40), textbooks: list.slice(0, 40), updated_at: new Date().toISOString() }, { onConflict: "user_id,grade" })
    : await q.delete().eq("user_id", sbUser.id).eq("grade", grade);
  if (error) console.warn("공유 출판사 저장", error.message);
}
// 내 데이터(exams.json)에 학교·학년·출판사 저장 + 지금 학년이면 공유
async function writeTb({ sch, view, isCur, list }) {   // sch: { name, id, addr, road }
  sch = { name: (sch.name || "").trim(), id: sch.id || "", addr: sch.addr || "", road: sch.road || "" }; list = cleanTb(list);
  await updateFile(EXAM_PATH, text => {
    let data; try { data = text ? JSON.parse(text) : { exams: [] }; } catch (e) { data = { exams: [] }; }
    data.exams ||= [];
    for (const [k, v] of [["school", sch.name], ["schoolId", sch.id], ["schoolAddr", sch.addr], ["schoolRoad", sch.road]]) if (v) data[k] = v; else delete data[k];
    const cur = savedTb(data) || { grade: "", textbooks: {} }, all = { ...cur.textbooks };
    if (list.length) all[view] = list; else delete all[view];
    data.textbooks = Object.fromEntries(GRADES.filter(g => all[g]).map(g => [g, all[g]]));
    data.grade = isCur ? view : cur.grade === view ? "" : cur.grade;
    return JSON.stringify(data, null, 2) + "\n";
  }, `앱에서 ${view} 교과서 출판사 수정`);
  examData = JSON.parse(files.get(EXAM_PATH).text); examData.exams ||= [];
  if (isCur) await pushShared(sch, view, list);
}
let tbView = store("tbgrade") || "";
const tbViewGrade = () => GRADES.includes(tbView) ? tbView : tbInfo().grade || "고1";
const subjKey = x => String(x || "").replace(/\s+/g, "");
function publisherOf(subj) {   // 지금 학년 목록에서: 같은 과목 이름 → 같은 과목 묶음 순
  const info = tbInfo(), list = info.textbooks[info.grade] || [];
  const hit = list.find(t => subjKey(t.subject) === subjKey(subj)) || list.find(t => subjectGroup(t.subject) === subjectGroup(subj));
  return (hit && hit.publisher) || "";
}
async function loadBooks(seq = loadSeq) {
  $("label").innerHTML = `교과서 출판사<span class="sub">우리 학교 · 학년별</span>`;
  $("view").innerHTML = `<div class="loading">불러오는 중…</div>`;
  try { await loadExamData(true); if (seq === loadSeq) renderBooks(); } catch (e) { if (seq === loadSeq) showError(e); }
}
function renderBooks() {
  if (tbDraft) { $("view").innerHTML = tbForm(tbDraft); return; }
  $("view").innerHTML = (SB && sbUser ? `<button class="add" data-act="xtbsetup" style="width:100%;background:var(--card);margin-bottom:10px">🏫 학교·학년 바꾸기 / 친구들이 등록한 출판사 보기</button>` : "")
    + tbCard() + `<div class="empty" style="padding:4px 6px 12px;font-size:13px">학년 버튼을 눌러 학년마다 따로 적을 수 있어요.
    ★ 표시한 지금 학년의 출판사가 📝 시험 범위·진도의 시험 카드에 나와요.</div>`;
}
function tbCard() {
  const info = tbInfo(), g = tbViewGrade(), list = info.textbooks[g] || [];
  return `<section class="day tbcard">${info.school ? `<div class="tbschool">🏫 ${esc(info.school)}${info.sch.addr || info.sch.road ? `<small>${esc(info.sch.addr || info.sch.road)}</small>` : ""}</div>` : ""}
    <div class="dhead"><span class="date">📚 ${g} 교과서 출판사</span>
    ${g === info.grade ? '<span class="chip">지금 학년</span>' : ""}<span class="sp"></span>
    <button class="pencil" data-act="xtbedit" aria-label="출판사 수정">✏️</button></div>
    <div class="tbgrades">${GRADES.map(x => `<button data-act="xtbg" data-g="${x}" class="${x === g ? "on" : ""}">${x}${x === info.grade ? " ★" : ""}</button>`).join("")}</div>
    ${list.length ? `<div class="tbgrid">${list.map(t => `<div><span>${esc(t.subject)}</span><b>${esc(t.publisher || "-")}</b></div>`).join("")}</div>`
      : `<div class="empty">✏️을 눌러 ${g} 과목별 출판사를 적어 보세요.</div>`}</section>`;
}
function tbForm(d) {
  const lv = d.view.startsWith("중") ? "중" : "고";
  const subj = [...new Set([...(d.isCur ? Object.values((schedule?.school || {}).timetable || {}).flat() : []), ...TB_SUBJ[lv]])];
  const missing = tbBase(d.view).filter(x => !d.list.some(t => subjKey(t.subject) === subjKey(x)));
  return `<section class="day editing rform">
    <div class="dhead"><span class="date">📚 ${d.view} 교과서 출판사</span></div>
    ${SB && sbUser ? `<label>학교</label><div class="tbpicked"><span><b>${esc(d.sch.name || "아직 안 정했어요")}</b>${d.sch.addr || d.sch.road ? `<small>${esc(d.sch.addr || d.sch.road)}</small>` : ""}</span>
      <button class="btn ghost" data-act="xtbsetup">🏫 학교 바꾸기</button></div>`
      : `<label>학교 이름 <span class="hint">— 선택</span></label><input data-tb="school" value="${esc(d.sch.name)}" placeholder="예) ○○고등학교">`}
    <datalist id="tbsubjects">${subj.map(x => `<option value="${esc(x)}">`).join("")}</datalist>
    <label class="tbcur"><input type="checkbox" data-tb="isCur" ${d.isCur ? "checked" : ""}><span><b>지금 내 학년이에요</b>
      <small>켜 두면 시험 카드에 이 학년 출판사가 나와요</small></span></label>
    <label>과목별 출판사</label>
    ${d.list.map((t, k) => `<div class="tbrow" data-k="${k}">
      <input data-tb="subject" list="tbsubjects" value="${esc(t.subject)}" placeholder="과목">
      <input data-tb="publisher" value="${esc(t.publisher)}" placeholder="출판사 (예: 비상)">
      <button class="del" data-act="xtbdel" aria-label="과목 삭제">×</button></div>`).join("")}
    <div style="display:flex;gap:8px">
      <button class="add" data-act="xtbadd" style="flex:1">+ 과목 추가</button>
      ${missing.length ? `<button class="add" data-act="xtbfill" style="flex:1">${d.view.startsWith("중") ? "중학교" : d.view} 기본 과목 넣기</button>` : ""}</div>
    <div class="actions" style="margin-top:12px">
      <button class="btn ghost" data-act="xtbcancel" ${saving ? "disabled" : ""}>취소</button>
      <button class="btn" data-act="xtbsave" ${saving ? "disabled" : ""}>${saving ? "저장 중…" : "저장"}</button>
    </div></section>`;
}
function tbInput(t) {
  const k = t.dataset.tb, row = t.closest(".tbrow");
  if (row) tbDraft.list[+row.dataset.k][k] = t.value;
  else if (k === "isCur") tbDraft.isCur = t.checked;
  else if (k === "school") tbDraft.sch = { name: t.value };
}
async function saveTextbooks() {
  const d = tbDraft;
  saving = true; renderBooks();
  try { await writeTb(d); tbDraft = null; toast(d.isCur && sharedKey(d.sch) && SB ? "저장됨 ✓ 우리 학교 친구들도 볼 수 있어요" : "저장됨 ✓"); }
  catch (e) { saving = false; renderBooks(); showError(e, true); return; }
  saving = false; renderBooks();
}
async function loadExamData(force) {
  const f = await getFile(EXAM_PATH, force);
  try { examData = f ? JSON.parse(f.text) : { exams: [] }; } catch (e) { examData = { exams: [] }; }
  examData.exams ||= [];
}
const examsOn = s => (examData.exams || []).filter(x => x.date === s);
const progressOf = x => x.ranges && x.ranges.length ? Math.round(x.ranges.reduce((a, r) => a + (+r.progress || 0), 0) / x.ranges.length) : 0;
const barCls = p => p >= 70 ? "" : p >= 30 ? "mid" : "low";
function ddayOf(s) {
  const n = Math.round((D(s) - D(todayKST())) / 864e5);
  return n === 0 ? ["D-DAY", "soon"] : n > 0 ? [`D-${n}`, n <= 7 ? "soon" : ""] : [`D+${-n}`, "past"];
}
async function loadExams(seq = loadSeq) {
  $("label").innerHTML = `시험 범위·진도<span class="sub">정기시험 · 수행평가</span>`;
  $("view").innerHTML = `<div class="loading">불러오는 중…</div>`;
  try { await loadExamData(true); await loadWeakData().catch(() => {}); if (seq === loadSeq) renderExams(); } catch (e) { if (seq === loadSeq) showError(e); }
}
function examCard(x) {
  const p = progressOf(x), [dd, ddc] = x.date ? ddayOf(x.date) : ["날짜 미정", "past"];
  return `<section class="day" data-id="${x.id}">
    <div class="dhead"><span class="xkind ${x.kind === "수행" ? "perf" : ""}">${x.kind === "수행" ? "수행평가" : "정기시험"}</span>
      <span class="date">${esc(x.subject || "")}</span>${publisherOf(x.subject) ? `<span class="chip">${esc(publisherOf(x.subject))}</span>` : ""}<span class="dday ${ddc}">${dd}</span><span class="sp"></span>
      <button class="pencil" data-act="xedit" aria-label="수정">✏️</button></div>
    <div class="empty" style="margin-top:2px">${esc(x.name || "")}${x.date ? ` · ${x.date.slice(5).replace("-", "/")} (${WD[wday(x.date)]})` : ""}</div>
    <div class="xr"><div class="top"><span>전체 진도</span><span class="pct">${p}%</span></div><div class="bar ${barCls(p)}"><i style="width:${p}%"></i></div></div>
    ${(x.ranges || []).map(r => `<div class="xr"><div class="top"><span>${esc(r.text)}</span><span class="pct">${+r.progress || 0}%</span></div>
      <div class="bar ${barCls(+r.progress || 0)}"><i style="width:${+r.progress || 0}%"></i></div>${r.memo ? `<div class="memo">${esc(r.memo)}</div>` : ""}</div>`).join("")}
    ${x.memo ? `<div class="rsec"><h3>메모</h3><div class="pre">${esc(x.memo)}</div></div>` : ""}
    ${(w => w.length ? `<div class="rsec"><h3>🩹 부족한 점 ${w.length}개</h3><ul>${w.slice(0, 5).map(k => `<li>${esc(k.text)}</li>`).join("")}${w.length > 5 ? `<li class="memo-i">…${w.length - 5}개 더 (☰ 메뉴 → 과목별 부족한 점)</li>` : ""}</ul></div>` : "")(weakOpen(x.subject))}
  </section>`;
}
function examForm(d) {
  const subj = [...new Set([...Object.values(school().timetable || {}).flat(), ...SUBJECTS])];
  return `<section class="day editing rform">
    <div class="dhead"><span class="date">${d.id ? "✏️ 시험 수정" : "📝 새 시험"}</span></div>
    <datalist id="subjects">${subj.map(x => `<option value="${esc(x)}">`).join("")}</datalist>
    <label>종류</label><select data-x="kind"><option value="정기" ${d.kind !== "수행" ? "selected" : ""}>정기시험</option><option value="수행" ${d.kind === "수행" ? "selected" : ""}>수행평가</option></select>
    <label>과목</label><input data-x="subject" list="subjects" value="${esc(d.subject)}" placeholder="예) 수학">
    <label>시험 이름</label><input data-x="name" value="${esc(d.name)}" placeholder="예) 2차 정기시험, 영어 말하기 수행">
    <label>날짜</label><input type="date" data-x="date" value="${esc(d.date)}">
    <label>📖 범위와 진도 <span class="hint">— 범위를 나눠 적고, 얼마나 공부했는지 0~100%</span></label>
    ${d.ranges.map((r, k) => `<div class="xrow" data-k="${k}">
      <input data-x="rtext" value="${esc(r.text)}" placeholder="범위 (예: 3단원 해수의 순환 p.80~95)">
      <button class="del" data-act="xrdel" aria-label="범위 삭제">×</button>
      <div class="sl"><input type="range" min="0" max="100" step="10" data-x="rprog" value="${+r.progress || 0}"><b>${+r.progress || 0}%</b></div>
      <input class="m" data-x="rmemo" value="${esc(r.memo || "")}" placeholder="메모 (예: 교과서 2회독, 문제집 남음)"></div>`).join("")}
    <button class="add" data-act="xradd" style="width:100%">+ 범위 추가</button>
    <label>메모</label><textarea data-x="memo" placeholder="시험 방식, 준비물 등">${esc(d.memo || "")}</textarea>
    <div class="actions" style="margin-top:12px">
      ${d.id ? `<button class="btn ghost danger" data-act="xdel" ${saving ? "disabled" : ""} style="margin-right:auto">🗑 삭제</button>` : ""}
      <button class="btn ghost" data-act="xcancel" ${saving ? "disabled" : ""}>취소</button>
      <button class="btn" data-act="xsave" ${saving ? "disabled" : ""}>${saving ? "저장 중…" : "저장"}</button>
    </div></section>`;
}
function renderExams() {
  if (examDraft) { $("view").innerHTML = examForm(examDraft); return; }
  const t = todayKST();
  const list = examData.exams.filter(x => examFilter === "all" || x.kind === examFilter)
    .sort((a, b) => (a.date || "9999").localeCompare(b.date || "9999"));
  const up = list.filter(x => !x.date || x.date >= t), past = list.filter(x => x.date && x.date < t).reverse();
  $("view").innerHTML = `<div class="kindbar">
      <button data-act="xfilter" data-f="all" class="${examFilter === "all" ? "on" : ""}">전체</button>
      <button data-act="xfilter" data-f="정기" class="${examFilter === "정기" ? "on" : ""}">📝 정기시험</button>
      <button data-act="xfilter" data-f="수행" class="${examFilter === "수행" ? "on" : ""}">🎯 수행평가</button></div>
    <div style="display:flex;gap:8px;margin-bottom:10px">
      <button class="add" data-act="xnew" style="flex:1;background:var(--card)">+ 시험 추가</button>
      <button class="add" data-act="xscan" style="flex:1;background:var(--card)">📥 계획에서 시험 찾기</button></div>
    ${examCands ? candPanel() : ""}
    ${up.length ? up.map(examCard).join("") : '<div class="day"><div class="empty">다가오는 시험이 없어요. + 시험 추가로 과목별 범위를 적어 보세요. (예: 2차 정기시험 12/9~12/15)</div></div>'}
    ${past.length ? `<button class="btn ghost" data-act="xpast" style="width:100%;margin:6px 0 10px">${examOpenPast ? "▲ 지난 시험 접기" : `▼ 지난 시험 ${past.length}개`}</button>${examOpenPast ? past.map(examCard).join("") : ""}` : ""}`;
}
function examInput(t) {
  const k = t.dataset.x, row = t.closest(".xrow");
  if (row) {
    const r = examDraft.ranges[+row.dataset.k];
    if (k === "rtext") r.text = t.value;
    else if (k === "rmemo") r.memo = t.value;
    else if (k === "rprog") { r.progress = +t.value; t.nextElementSibling.textContent = t.value + "%"; }
  } else examDraft[k] = t.value;
}
$("view").addEventListener("change", ev => { if (examDraft && ev.target.dataset.x === "kind") examDraft.kind = ev.target.value; });
// 학사일정의 시험날 + 계획표·보고서에 적힌 수행/시험/평가 를 찾아 후보로 보여줌
async function scanExams() {
  const out = [], seen = new Set(), t = todayKST();
  const have = x => examData.exams.some(e => e.date === x.date && (subjectGroup(e.subject) === subjectGroup(x.subject) || e.name === x.name));
  const add = x => { const k = x.date + "|" + (subjectGroup(x.subject) || x.name); if (seen.has(k) || have(x) || x.date < addDays(t, -7)) return; seen.add(k); out.push(x); };
  // 1) 학사일정 시험날 → 이어진 날짜를 하나의 정기시험으로
  const ed = Object.entries(school().exam_days || {}).sort();
  for (let i = 0; i < ed.length;) {
    let j = i; while (j + 1 < ed.length && ed[j + 1][1] === ed[i][1] && (D(ed[j + 1][0]) - D(ed[j][0])) / 864e5 <= 4) j++;
    const dates = ed.slice(i, j + 1).map(e => e[0]);
    const subs = [...new Set(Object.values(school().timetable || {}).flat())].filter(x => !/창체|동아리|진로|체육|미술|음악/.test(x));
    add({ kind: "정기", subject: "전 과목", name: ed[i][1], date: dates[0], src: "학사일정",
      memo: "시험 날짜: " + dates.map(d => `${+d.slice(5, 7)}/${+d.slice(8)}(${WD[wday(d)]})`).join(", "),
      ranges: subs.map(x => ({ text: x, progress: 0, memo: "" })) });
    i = j + 1;
  }
  // 2) 계획표(주간·월간)의 일정·할 일
  const KW = /수행|시험|평가/, NO = /수능|모의|예비소집|정기시험|학교 안 감|^✏️|^🏫/;
  for (const p of [...files.keys()].filter(p => /^plans\/(week|month)\//.test(p))) {
    const f = files.get(p); if (!f) continue;
    const ref = p.includes("/week/") ? p.slice(11, 21) : p.slice(12, 19) + "-01";
    const tbl = parseTable(f.text, ref);
    for (const [d, day] of Object.entries(tbl))
      for (const it of [...day.events.map(e => e.title), ...day.memos.map(taskText)])
        if (KW.test(it) && !NO.test(it)) add({ kind: /정기|중간|기말/.test(it) ? "정기" : "수행", subject: guessSubject(it), name: it, date: d, src: "계획표", memo: "", ranges: [] });
  }
  // 3) 보고서의 '기억해야 할 것' 등에 적힌 날짜 + 수행
  for (const p of [...files.keys()].filter(p => p.startsWith("plans/report/"))) {
    const f = files.get(p); if (!f) continue;
    const r = parseReport(f.text), y = +p.slice(13, 17);
    for (const line of [r.remember, r.important, r.etc, r.memorize].join("\n").split("\n")) {
      let cur = null;
      for (const piece of line.split(/[,，]/)) {
        const m = piece.match(/(\d{1,2})\s*\/\s*(\d{1,2})/);
        if (m) cur = `${y}-${pad(+m[1])}-${pad(+m[2])}`;
        if (cur && KW.test(piece) && !NO.test(piece)) {
          const name = piece.replace(/\d{1,2}\s*\/\s*\d{1,2}/, "").trim();
          add({ kind: "수행", subject: guessSubject(piece), name, date: cur, src: "보고서", memo: "", ranges: [] });
        }
      }
    }
  }
  return out.sort((a, b) => a.date.localeCompare(b.date));
}
const candPanel = () => `<section class="day editing"><div class="dhead"><span class="date">📥 계획에서 찾은 시험</span></div>
  ${examCands.length ? examCands.map((c, k) => `<label class="cand"><input type="checkbox" data-k="${k}" checked>
    <div><b>${c.kind === "정기" ? "📝 정기" : "🎯 수행"} · ${esc(c.subject || "과목?")}</b> ${esc(c.name)}
    <div class="src">${c.date.slice(5).replace("-", "/")} (${WD[wday(c.date)]}) · ${c.src}에서 찾음</div></div></label>`).join("")
    : '<div class="empty">새로 등록할 시험을 못 찾았어요. (이미 등록됐거나, 계획에 "수행·시험·평가"라는 말이 없어요)</div>'}
  <div class="actions" style="margin-top:8px"><button class="btn ghost" data-act="xscancel">닫기</button>
    ${examCands.length ? `<button class="btn" data-act="xsadd" ${saving ? "disabled" : ""}>${saving ? "저장 중…" : "선택한 것 등록"}</button>` : ""}</div></section>`;
async function examClick(b) {
  const act = b.dataset.act;
  if (act === "xscan") { examCands = await scanExams(); return renderExams(); }
  if (act === "xscancel") { examCands = null; return renderExams(); }
  if (act === "xsadd") {
    const pick = [...document.querySelectorAll(".cand input")].filter(i => i.checked).map(i => examCands[+i.dataset.k]);
    if (!pick.length) return toast("고른 게 없어요");
    saving = true; renderExams();
    try {
      await updateFile(EXAM_PATH, text => {
        let data; try { data = text ? JSON.parse(text) : { exams: [] }; } catch (e) { data = { exams: [] }; }
        data.exams ||= [];
        pick.forEach((c, k) => data.exams.push({ id: "x" + Date.now().toString(36) + k, kind: c.kind, subject: c.subject, name: c.name, date: c.date, ranges: c.ranges, memo: c.memo }));
        data.exams.sort((a, b) => (a.date || "9999").localeCompare(b.date || "9999"));
        return JSON.stringify(data, null, 2) + "\n";
      }, `앱에서 계획의 시험 ${pick.length}개 등록`);
      examData = JSON.parse(files.get(EXAM_PATH).text); examCands = null; toast(`✓ ${pick.length}개 등록했어요`);
    } catch (e) { saving = false; renderExams(); showError(e, true); return; }
    saving = false; return renderExams();
  }
  if (act === "xtbg") { if (!leaveOk()) return; tbView = b.dataset.g; store("tbgrade", tbView); return renderBooks(); }
  if (act === "xtbedit") {
    if (!leaveOk()) return;
    const info = tbInfo(), view = tbViewGrade();
    tbDraft = { view, sch: { ...info.sch }, isCur: info.grade === view || !info.grade, list: structuredClone(info.textbooks[view] || []) };
    if (!tbDraft.list.length) tbDraft.list = tbBase(view).map(x => ({ subject: x, publisher: "" }));
    renderBooks(); return window.scrollTo({ top: 0 });
  }
  if (act === "xtbfill") { tbBase(tbDraft.view).filter(x => !tbDraft.list.some(t => subjKey(t.subject) === subjKey(x))).forEach(x => tbDraft.list.push({ subject: x, publisher: "" })); return renderBooks(); }
  if (act === "xtbcancel") { tbDraft = null; return renderBooks(); }
  if (act === "xtbadd") { tbDraft.list.push({ subject: "", publisher: "" }); renderBooks(); return [...document.querySelectorAll('.tbrow [data-tb="subject"]')].pop()?.focus(); }
  if (act === "xtbdel") { tbDraft.list.splice(+b.closest(".tbrow").dataset.k, 1); return renderBooks(); }
  if (act === "xtbsave") return saveTextbooks();
  if (act === "xtbsetup") { if (!leaveOk()) return; tbDraft = null; return showSchoolSetup(); }
  if (act === "xfilter") { examFilter = b.dataset.f; return renderExams(); }
  if (act === "xpast") { examOpenPast = !examOpenPast; return renderExams(); }
  if (act === "xnew") { if (!leaveOk()) return; examDraft = { kind: "정기", subject: "", name: "", date: "", ranges: [{ text: "", progress: 0, memo: "" }], memo: "" }; }
  else if (act === "xedit") { if (!leaveOk()) return; const id = b.closest("[data-id]").dataset.id; examDraft = structuredClone(examData.exams.find(x => x.id === id)); examDraft.ranges ||= []; }
  else if (act === "xcancel") examDraft = null;
  else if (act === "xradd") examDraft.ranges.push({ text: "", progress: 0, memo: "" });
  else if (act === "xrdel") examDraft.ranges.splice(+b.closest(".xrow").dataset.k, 1);
  else if (act === "xsave") return saveExam(false);
  else if (act === "xdel") { if (!confirm("이 시험을 지울까요?")) return; return saveExam(true); }
  renderExams();
  if (act === "xnew" || act === "xedit") window.scrollTo({ top: 0 });
  if (act === "xradd") [...document.querySelectorAll('.xrow [data-x="rtext"]')].pop()?.focus();
}
async function saveExam(remove) {
  const d = examDraft;
  if (!remove && !(d.subject || d.name || "").trim()) { toast("과목이나 시험 이름을 적어 주세요"); return; }
  const clean = { ...d, id: d.id || "x" + Date.now().toString(36), subject: (d.subject || "").trim(), name: (d.name || "").trim(),
    ranges: d.ranges.filter(r => (r.text || "").trim()).map(r => ({ text: r.text.trim(), progress: Math.max(0, Math.min(100, +r.progress || 0)), memo: (r.memo || "").trim() })) };
  saving = true; renderExams();
  try {
    await updateFile(EXAM_PATH, text => {
      let data; try { data = text ? JSON.parse(text) : { exams: [] }; } catch (e) { data = { exams: [] }; }
      data.exams = (data.exams || []).filter(x => x.id !== clean.id);
      if (!remove) data.exams.push(clean);
      data.exams.sort((a, b) => (a.date || "9999").localeCompare(b.date || "9999"));
      return JSON.stringify(data, null, 2) + "\n";
    }, `앱에서 시험 ${remove ? "삭제" : d.id ? "수정" : "추가"}: ${clean.subject} ${clean.name}`.trim());
    examData = JSON.parse(files.get(EXAM_PATH).text); examDraft = null; toast(remove ? "지웠어요" : "저장됨 ✓");
  } catch (e) { saving = false; renderExams(); showError(e, true); return; }
  saving = false; renderExams();
}

/* ---------- 🩹 과목별 부족한 점 (plans/weak.json) ----------
   { items: [{ id, subject, text, memo, done, date }] }  과목마다 모르는 것·자주 틀리는 것을 적어 두고, 알게 되면 ✓ 해결 */
const WEAK_PATH = "plans/weak.json";
let weakData = { items: [] }, weakDraft = null, weakSubj = store("wksubj") || "all", weakOpenDone = false;
async function loadWeakData(force) {
  const f = await getFile(WEAK_PATH, force);
  try { weakData = f ? JSON.parse(f.text) : { items: [] }; } catch (e) { weakData = { items: [] }; }
  if (!Array.isArray(weakData.items)) weakData.items = [];
}
const weakOpen = subj => weakData.items.filter(w => !w.done && subjKey(w.subject) === subjKey(subj));
async function loadWeak(seq = loadSeq) {
  $("label").innerHTML = `과목별 부족한 점<span class="sub">모르는 것 · 자주 틀리는 것</span>`;
  $("view").innerHTML = `<div class="loading">불러오는 중…</div>`;
  try { await loadWeakData(true); await loadExamData().catch(() => {}); if (seq === loadSeq) renderWeak(); } catch (e) { if (seq === loadSeq) showError(e); }
}
function weakSubjects() {   // 적어 둔 과목 + 시간표 과목 + 기본 과목
  return [...new Set([...weakData.items.map(w => w.subject), ...Object.values(school().timetable || {}).flat(), ...SUBJECTS].filter(Boolean))];
}
function weakForm(d) {
  return `<section class="day editing rform">
    <div class="dhead"><span class="date">${d.id ? "✏️ 부족한 점 고치기" : "🩹 부족한 점 적기"}</span></div>
    <datalist id="wsubjects">${weakSubjects().map(x => `<option value="${esc(x)}">`).join("")}</datalist>
    <label>과목</label><input data-wk="subject" list="wsubjects" value="${esc(d.subject)}" placeholder="예) 수학">
    <label>부족한 점 <span class="hint">— 모르는 개념, 자주 틀리는 유형</span></label>
    <input data-wk="text" value="${esc(d.text)}" placeholder="예) 이차함수 꼭짓점 구하기에서 부호 실수">
    <label>메모 <span class="hint">— 어떻게 보완할지, 참고할 쪽수</span></label>
    <textarea data-wk="memo" placeholder="예) 쎈 p.42~45 다시 풀기, 오답노트에 정리">${esc(d.memo || "")}</textarea>
    <label class="tbcur" style="margin-top:12px"><input type="checkbox" data-wk="done" ${d.done ? "checked" : ""}><span>✓ 해결했어요<small>이제 알게 됐으면 체크 (지우지 않고 '해결한 것'에 남아요)</small></span></label>
    <div class="actions" style="margin-top:12px">
      ${d.id ? `<button class="btn ghost danger" data-act="Kdel" ${saving ? "disabled" : ""} style="margin-right:auto">🗑 삭제</button>` : ""}
      <button class="btn ghost" data-act="Kcancel" ${saving ? "disabled" : ""}>취소</button>
      <button class="btn" data-act="Ksave" ${saving ? "disabled" : ""}>${saving ? "저장 중…" : "저장"}</button>
    </div></section>`;
}
const weakItem = w => `<li class="task${w.done ? " done" : ""}" data-id="${esc(w.id)}">
    <button class="chk${w.done ? " on" : ""}" data-act="Kchk" aria-label="${w.done ? "다시 부족한 점으로" : "해결 표시"}">${w.done ? "✓" : ""}</button>
    <span style="flex:1;min-width:0"><span>${esc(w.text)}</span>${w.memo ? `<span class="memo-i pre" style="display:block;font-size:12px;text-decoration:none">${esc(w.memo)}</span>` : ""}</span>
    <button class="pencil" data-act="Kedit" aria-label="수정" title="수정">✏️</button></li>`;
function renderWeak() {
  if (weakDraft) { $("view").innerHTML = weakForm(weakDraft); return; }
  const all = weakData.items, keys = [...new Set(all.map(w => w.subject))];
  if (weakSubj !== "all" && !keys.includes(weakSubj)) weakSubj = "all";
  const list = all.filter(w => weakSubj === "all" || w.subject === weakSubj);
  const open = list.filter(w => !w.done), done = list.filter(w => w.done);
  const groups = [...new Set(open.map(w => w.subject))];
  const cnt = s => all.filter(w => !w.done && (s === "all" || w.subject === s)).length;
  $("view").innerHTML = `
    ${keys.length ? `<div class="filters"><button data-act="Kfilter" data-f="all" class="${weakSubj === "all" ? "on" : ""}">전체 ${cnt("all")}</button>
      ${keys.map(s => `<button data-act="Kfilter" data-f="${esc(s)}" class="${weakSubj === s ? "on" : ""}">${esc(s)} ${cnt(s)}</button>`).join("")}</div>` : ""}
    <button class="add" data-act="Knew" style="width:100%;background:var(--card);margin-bottom:10px">+ 부족한 점 적기</button>
    ${groups.length ? groups.map(s => {
      const xs = open.filter(w => w.subject === s), ex = examData.exams.find(x => subjKey(x.subject) === subjKey(s) && x.date && x.date >= todayKST());
      return `<section class="day"><div class="dhead"><span class="date">${esc(s)}</span><span class="chip">${xs.length}개</span>
        ${ex ? `<span class="dday ${ddayOf(ex.date)[1]}" title="${esc(ex.name || "시험")}">${ddayOf(ex.date)[0]}</span>` : ""}<span class="sp"></span></div>
        <ul class="list tasks">${xs.map(weakItem).join("")}</ul></section>`;
    }).join("") : `<div class="day"><div class="empty">${all.length ? "남은 부족한 점이 없어요 🎉" : "과목마다 모르는 개념, 자주 틀리는 유형을 적어 두세요. 알게 되면 체크해서 해결한 것으로 옮겨요."}</div></div>`}
    ${done.length ? `<button class="btn ghost" data-act="Kpast" style="width:100%;margin:6px 0 10px">${weakOpenDone ? "▲ 해결한 것 접기" : `▼ 해결한 것 ${done.length}개`}</button>
      ${weakOpenDone ? `<section class="day"><ul class="list tasks">${done.map(w => weakItem({ ...w, text: (weakSubj === "all" ? `[${w.subject}] ` : "") + w.text })).join("")}</ul></section>` : ""}` : ""}`;
}
async function writeWeak(fn, msg, okMsg) {
  saving = true; renderWeak();
  try {
    await updateFile(WEAK_PATH, text => {
      let data; try { data = text ? JSON.parse(text) : { items: [] }; } catch (e) { data = { items: [] }; }
      data.items = fn(Array.isArray(data.items) ? data.items : []);
      return JSON.stringify(data, null, 2) + "\n";
    }, msg);
    weakData = JSON.parse(files.get(WEAK_PATH).text); weakDraft = null; if (okMsg) toast(okMsg);
  } catch (e) { saving = false; renderWeak(); showError(e, true); return; }
  saving = false; renderWeak();
}
function weakClick(b) {
  const act = b.dataset.act, id = b.closest("[data-id]")?.dataset.id;
  if (act === "Kfilter") { weakSubj = b.dataset.f; store("wksubj", weakSubj); return renderWeak(); }
  if (act === "Kpast") { weakOpenDone = !weakOpenDone; return renderWeak(); }
  if (act === "Kchk") {   // 해결 체크는 바로 저장
    const w = weakData.items.find(x => x.id === id); if (!w) return;
    const done = !w.done;
    return writeWeak(list => list.map(x => x.id === id ? { ...x, done } : x), "앱에서 부족한 점 체크", done ? "✓ 해결! 잘했어요" : "다시 부족한 점으로 옮겼어요");
  }
  if (act === "Knew") { if (!leaveOk()) return; weakDraft = { subject: weakSubj === "all" ? "" : weakSubj, text: "", memo: "", done: false }; }
  else if (act === "Kedit") { if (!leaveOk()) return; weakDraft = structuredClone(weakData.items.find(x => x.id === id)); if (!weakDraft) return; }
  else if (act === "Kcancel") weakDraft = null;
  else if (act === "Kdel") {
    if (!confirm("이 부족한 점을 지울까요?")) return;
    const did = weakDraft.id; return writeWeak(list => list.filter(x => x.id !== did), "앱에서 부족한 점 삭제", "지웠어요");
  } else if (act === "Ksave") {
    const d = weakDraft, subject = cleanText(d.subject), text = (d.text || "").trim();
    if (!subject) return toast("과목을 적어 주세요");
    if (!text) return toast("부족한 점을 적어 주세요");
    const w = { id: d.id || "k" + Date.now().toString(36), subject, text: text.slice(0, 300), memo: (d.memo || "").trim().slice(0, 2000), done: !!d.done, date: d.date || todayKST() };
    return writeWeak(list => d.id ? list.map(x => x.id === w.id ? w : x) : [...list, w], `앱에서 부족한 점 ${d.id ? "수정" : "추가"}: ${subject}`, "저장됨 ✓");
  }
  renderWeak();
  if (act === "Knew" || act === "Kedit") { window.scrollTo({ top: 0 }); document.querySelector(`[data-wk="${act === "Knew" && weakDraft.subject ? "text" : "subject"}"]`)?.focus(); }
}

/* ---------- 뉴스 · 공지 ----------
   docs/news.json            : 최근 기사 (GitHub Actions 가 3시간마다 구글 뉴스에서 모음, 기사마다 처음 들어온 시각 added)
   docs/news/<분야>/<연도>.json : 2000년 ~ 지금 기사 보관함, docs/news/index.json : 분야·연도별 기사 수
   새 기사는 들어온 지 5시간(notice_hours) 동안 📢 공지에서 먼저 보여 주고, 그 뒤엔 📰 뉴스 탭에 같이 보여요. */
const NEWS_PAGE = 100;
let newsData = null, newsIndex = null, newsCat = store("ncat") || "stock", newsQuery = "", newsYear = "", newsMonth = "", newsShow = NEWS_PAGE;
const newsYearCache = {};
const newsCats = () => (newsData && newsData.categories) || [];
const noticeMs = () => ((newsData && newsData.notice_hours) || 5) * 36e5;
const isNotice = x => !!x.added && Date.now() - new Date(x.added) < noticeMs();
async function fetchNews(force) {
  if (newsData && !force && Date.now() - fetchNews.at < 5 * 6e4) return newsData;
  try {
    const r = await fetch("news.json?v=" + Date.now(), { cache: "no-store" });
    if (r.ok) { newsData = await r.json(); fetchNews.at = Date.now(); }
  } catch (e) {}
  if (!newsData) newsData = { categories: [] };
  updateNoticeBadge();
  return newsData;
}
fetchNews.at = 0;
const noticeGroups = () => newsCats().map(c => ({ ...c, items: c.items.filter(isNotice) })).filter(c => c.items.length);
function updateNoticeBadge() {
  const seen = store("nseen") || "";
  const n = noticeGroups().reduce((s, c) => s + c.items.filter(x => x.added > seen).length, 0);
  const el = $("noticeCnt");
  el.hidden = !n; el.textContent = n > 99 ? "99+" : n;
  $("noticeBtn").title = n ? `공지: 새 뉴스 ${n}건` : "공지 (새 뉴스)";
}
function agoText(t) {
  if (!t) return "";
  const m = Math.round((Date.now() - new Date(t)) / 6e4);
  return m < 1 ? "방금" : m < 60 ? `${m}분 전` : m < 1440 ? `${Math.floor(m / 60)}시간 전` : `${Math.floor(m / 1440)}일 전`;
}
const kstHM = d => d.toLocaleTimeString("ko-KR", { timeZone: "Asia/Seoul", hour: "2-digit", minute: "2-digit", hour12: false });
// 회사 분야는 이모지 대신 진짜 로고 그림을 보여 줘요 (docs/logos/키.png)
const NEWS_LOGOS = new Set(["nation", "samsung", "nvidia", "apple", "hynix", "lg", "meta"]);
const catName = c => NEWS_LOGOS.has(c.key)
  ? `<img class="nlogo" src="logos/${c.key}.png" alt="">${esc(String(c.name).replace(/^\S+\s+/, ""))}`
  : esc(c.name);
const newsLink = (x, meta) => `<a href="${esc(safeUrl(x.link))}" target="_blank" rel="noopener noreferrer"><b>${esc(x.title)}</b><span>${esc(x.source || "")}${meta ? " · " + meta : ""}</span></a>`;

/* 📢 공지 */
async function loadNotice(seq = loadSeq) {
  $("label").innerHTML = `공지<span class="sub">안내 · 새로 들어온 뉴스</span>`;
  $("view").innerHTML = `<div class="loading">불러오는 중…</div>`;
  await fetchNews(true);
  if (seq === loadSeq) renderNotice();
}
function renderNotice() {
  const groups = noticeGroups(), up = newsData.updated, hrs = newsData.notice_hours || 5;
  const next = up ? new Date(new Date(up).getTime() + 3 * 36e5) : null;
  const left = x => { const m = Math.max(1, Math.ceil((new Date(x.added).getTime() + noticeMs() - Date.now()) / 6e4)); return m >= 60 ? `${Math.floor(m / 60)}시간 ${m % 60}분` : `${m}분`; };
  $("view").innerHTML = `<section class="day"><div class="dhead"><span class="date">📢 안내</span><span class="sp"></span><span class="empty" style="margin:0">${up ? agoText(up) + " 업데이트" : ""}</span></div>
      <div style="font-size:14px;line-height:1.65">새 뉴스는 <b>3시간마다</b> 들어와요. 들어온 지 <b>${hrs}시간</b> 동안은 여기 공지에서 먼저 보여 주고, 그 뒤에는 📰 뉴스 탭에서 다른 기사들과 같이 볼 수 있어요.
      <br>지난 기사는 📰 뉴스 탭에서 연도(2000년~)를 골라 볼 수 있어요.${next ? `<br>다음 업데이트: ${next > Date.now() ? kstHM(next) + " 쯤" : "곧"}` : ""}</div>
      <button class="btn ghost nmore" data-act="ngonews">📰 뉴스 탭으로</button></section>
    ${groups.length ? groups.map(c => `<section class="day"><div class="dhead"><span class="date">🆕 ${catName(c)}</span><span class="badge">${c.items.length}</span></div>
      <div class="nlist">${c.items.map(x => newsLink(x, `${x.time ? agoText(x.time) + " · " : ""}${left(x)} 뒤 뉴스 탭으로`)).join("")}</div></section>`).join("")
      : `<section class="day"><div class="empty">지금은 새로 들어온 뉴스가 없어요. 다음 업데이트 때 여기에 먼저 보여요.</div></section>`}`;
  const newest = groups.flatMap(c => c.items.map(x => x.added)).sort().pop();
  if (newest && newest > (store("nseen") || "")) store("nseen", newest);
  updateNoticeBadge();
}

/* 📰 뉴스 */
async function loadNews(seq = loadSeq) {
  $("label").innerHTML = `뉴스<span class="sub">분야별 · 기업별 뉴스 · 2000년~</span>`;
  $("view").innerHTML = `<div class="loading">뉴스 불러오는 중…</div>`;
  const [, idx] = await Promise.all([fetchNews(true),
    fetch("news/index.json?v=" + Date.now(), { cache: "no-store" }).then(r => r.ok ? r.json() : null).catch(() => null)]);
  newsIndex = idx;
  if (seq === loadSeq) renderNews();
}
function newsYears(key) {
  const y = (newsIndex && newsIndex.categories && newsIndex.categories[key] && newsIndex.categories[key].years) || {};
  return Object.keys(y).filter(k => y[k] > 0).sort().reverse().map(k => [k, y[k]]);
}
async function loadNewsYear(key, y) {
  const k = key + "/" + y;
  if (!newsYearCache[k]) {
    try {
      const r = await fetch(`news/${k}.json?v=${encodeURIComponent((newsIndex && newsIndex.updated) || Date.now())}`);
      newsYearCache[k] = r.ok ? ((await r.json()).items || []) : [];
    } catch (e) { return []; }
  }
  return newsYearCache[k];
}
function renderNews() {
  const cats = newsCats();
  if (!cats.length) { $("view").innerHTML = `<section class="day"><div class="empty">아직 모은 뉴스가 없어요. 조금 뒤에 다시 열어 보세요.<br>(GitHub → Actions → "뉴스 모으기" → Run workflow 로 바로 모을 수 있어요)</div></section>`; return; }
  if (!cats.some(c => c.key === newsCat)) newsCat = cats[0].key;
  const cat = cats.find(c => c.key === newsCat), years = newsYears(cat.key);
  if (newsYear && !years.some(([y]) => y === newsYear)) newsYear = "";
  const nn = cat.items.filter(isNotice).length;
  const mons = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, "0"));
  $("view").innerHTML = `<div class="kindbar nkinds">${cats.map(c => `<button data-act="ncat" data-k="${esc(c.key)}" class="${c.key === newsCat ? "on" : ""}">${catName(c)}</button>`).join("")}</div>
    ${nn && !newsYear ? `<button class="nnote" data-act="ngonotice">📢 새 뉴스 ${nn}건은 지금 공지에서 먼저 보여요 → <span style="font-weight:400">(들어온 지 5시간 뒤 여기로 와요)</span></button>` : ""}
    <div class="npick"><select id="nyear" aria-label="기간">
      <option value="">🕒 최근 30일</option>${years.map(([y, n]) => `<option value="${y}"${y === newsYear ? " selected" : ""}>${y}년 (${n.toLocaleString()}개)</option>`).join("")}</select>
      ${newsYear ? `<select id="nmonth" aria-label="달"><option value="">전체 달</option>${mons.map(m => `<option value="${m}"${m === newsMonth ? " selected" : ""}>${+m}월</option>`).join("")}</select>` : ""}</div>
    <input class="search" id="nsearch" value="${esc(newsQuery)}" placeholder="🔍 이 분야에서 찾기 (예: 금리, 반도체)">
    <section class="day"><div class="dhead"><span class="date">${catName(cat)}${newsYear ? ` · ${newsYear}년` + (newsMonth ? ` ${+newsMonth}월` : "") : ""}</span><span class="sp"></span><span class="empty" style="margin:0">${newsData.updated ? agoText(newsData.updated) + " 업데이트" : ""}</span></div>
      <div id="nres"></div>
      <div class="empty" style="font-size:12px">구글 뉴스에서 3시간마다 모으고, 2000년부터의 지난 기사도 연도별로 모아 둬요. 제목을 누르면 언론사 기사로 가요.</div></section>`;
  const inp = $("nsearch");
  inp.oninput = () => { newsQuery = inp.value; newsShow = NEWS_PAGE; newsList(); };   // 목록만 다시 그려서 한글 입력이 끊기지 않게
  $("nyear").onchange = e => { newsYear = e.target.value; newsMonth = ""; newsShow = NEWS_PAGE; renderNews(); };
  if ($("nmonth")) $("nmonth").onchange = e => { newsMonth = e.target.value; newsShow = NEWS_PAGE; renderNews(); };
  newsList();
}
async function newsList() {
  const cat = newsCats().find(c => c.key === newsCat), box = $("nres");
  if (!cat || !box) return;
  const y = newsYear, q = newsQuery.trim().toLowerCase();
  let items;
  if (y) {
    const k = cat.key + "/" + y;
    if (!newsYearCache[k]) box.innerHTML = `<div class="loading" style="padding:16px 0">${y}년 기사 불러오는 중…</div>`;
    items = await loadNewsYear(cat.key, y);
    if (y !== newsYear || cat.key !== newsCat || mode !== "news" || !$("nres")) return;
    const fresh = new Set(cat.items.filter(isNotice).map(x => x.link));   // 공지 기간인 기사는 공지에서
    items = items.filter(x => !fresh.has(x.link) && (!newsMonth || x.time.slice(5, 7) === newsMonth));
  } else items = cat.items.filter(x => !isNotice(x));
  if (q) items = items.filter(x => (x.title + " " + x.source).toLowerCase().includes(q));
  const when = x => !x.time ? "" : y ? x.time.slice(0, 10).replace(/-/g, ".") : agoText(x.time);
  $("nres").innerHTML = items.length
    ? `<div class="nlist">${items.slice(0, newsShow).map(x => newsLink(x, when(x))).join("")}</div>
       ${items.length > newsShow ? `<button class="btn ghost nmore" data-act="nmore">더 보기 (${(items.length - newsShow).toLocaleString()}개 더)</button>` : ""}`
    : `<div class="empty">${q ? "찾는 기사가 없어요." : y ? "이 기간 기사는 아직 모으는 중이에요." : "기사가 없어요."}</div>`;
}

/* ---------- 🔎 찾아보기 (인터넷 검색: 위키백과 바로 보기 + 검색 사이트 바로가기 + 나에게 맞춘 추천 검색어) ---------- */
// 🔒 검색어는 위키백과(ko.wikipedia.org)에만 보내고, 다른 사이트는 내가 버튼을 누를 때만 새 창으로 열려요
const WEB_SITES = [
  { g: "정보", items: [
    ["구글", "https://www.google.com/search?q="], ["네이버", "https://search.naver.com/search.naver?query="],
    ["다음", "https://search.daum.net/search?q="], ["나무위키", "https://namu.wiki/Search?q="],
    ["위키백과", "https://ko.wikipedia.org/w/index.php?search="], ["유튜브", "https://www.youtube.com/results?search_query="]] },
  { g: "공부", items: [
    ["EBSi", "https://www.ebsi.co.kr/ebs/xip/xipa/retrieveSearchResult.ebs?searchKeyword="], ["네이버 지식백과", "https://terms.naver.com/search.naver?query="],
    ["국어사전", "https://ko.dict.naver.com/#/search?query="], ["영어사전", "https://en.dict.naver.com/#/search?query="],
    ["구글 학술검색", "https://scholar.google.co.kr/scholar?q="], ["파파고 번역", "https://papago.naver.com/?sk=auto&tk=ko&st="]] },
  { g: "쇼핑·가격", items: [
    ["네이버 쇼핑", "https://search.shopping.naver.com/search/all?query="], ["쿠팡", "https://www.coupang.com/np/search?q="],
    ["다나와 최저가", "https://search.danawa.com/dsearch.php?query="], ["11번가", "https://search.11st.co.kr/Search.tmall?kwd="],
    ["G마켓", "https://browse.gmarket.co.kr/search?keyword="], ["당근 중고", "https://www.daangn.com/search/"]] },
  { g: "생활", items: [
    ["지도에서 찾기", "https://map.kakao.com/?q="], ["날씨", "https://search.naver.com/search.naver?query=날씨+"],
    ["맛집", "https://search.naver.com/search.naver?query=맛집+"], ["레시피", "https://www.10000recipe.com/recipe/list.html?q="]] },
];
let webQuery = "", webRes = null, webBusy = false, webSeq = 0;
const webRecent = () => { try { const a = JSON.parse(store("wrecent") || "[]"); return Array.isArray(a) ? a.filter(x => typeof x === "string").slice(0, 10) : []; } catch (e) { return []; } };
const webLink = (base, q) => safeUrl(base + encodeURIComponent(q));
const stripTags = s => String(s || "").replace(/<[^>]*>/g, "").replace(/&quot;/g, '"').replace(/&#039;|&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");

// 내 일정·시험·할 일에서 "지금 나에게 필요할 것 같은" 검색어 만들기
function webSuggest() {
  const out = [], add = (q, why) => { q = q.replace(/\s+/g, " ").trim(); if (q && q.length <= 40 && !out.some(x => x.q === q)) out.push({ q, why }); };
  const t = todayKST();
  const soon = (examData.exams || []).filter(x => x.date >= t && x.date <= addDays(t, 30)).sort((a, b) => a.date.localeCompare(b.date));
  for (const x of soon.slice(0, 4)) {
    const [dd] = ddayOf(x.date), subj = x.subject || x.name || "";
    const low = (x.ranges || []).filter(r => (+r.progress || 0) < 70).slice(0, 2);
    for (const r of low) add(`${subj} ${r.text} 개념 정리`, `📝 ${dd} · 진도 ${+r.progress || 0}%`);
    if (x.kind === "수행") add(`${x.name || subj} 수행평가 예시`, `📝 ${dd} 수행평가`);
    else add(`${subj} 기출문제`, `📝 ${dd} ${x.name || "시험"}`);
  }
  const td = days.find(d => d.iso === t);
  for (const m of ((td && td.day.memos) || []).filter(m => !isSys(m) && !isDone(m)).slice(0, 3)) add(taskText(m), "☑️ 오늘 할 일");
  try { const L = learnData && curLang(); if (L) add(`${L.name.replace(/^\S+\s/, "")} 기초 문법`, "💻 코딩 공부 중"); } catch (e) {}
  return out.slice(0, 8);
}

async function loadWeb(seq = loadSeq) {
  $("label").innerHTML = `찾아보기<span class="sub">인터넷 검색 · 나에게 맞춘 추천</span>`;
  $("view").innerHTML = `<div class="loading">불러오는 중…</div>`;
  try { await loadExamData(); } catch (e) {}
  if (seq !== loadSeq) return;
  renderWeb();
}
function renderWeb() {
  const q = webQuery.trim(), sug = webSuggest(), rec = webRecent();
  $("view").innerHTML = `<form class="wform" id="wform"><input class="search" id="wq" type="search" enterkeyhint="search" value="${esc(webQuery)}" placeholder="🔎 무엇이든 찾아보기 (예: 광합성, 무선 이어폰, 파이썬 반복문)" autocomplete="off">
      <button class="btn" type="submit">검색</button></form>
    ${q ? "" : `${sug.length ? `<section class="day"><div class="dhead"><span class="date">✨ 나에게 필요할 것 같은 검색</span></div>
      <div class="wsug">${sug.map(s => `<button data-act="wgo" data-q="${esc(s.q)}"><b>${esc(s.q)}</b><span>${esc(s.why)}</span></button>`).join("")}</div>
      <div class="empty" style="font-size:12px">다가오는 시험(진도가 낮은 범위), 오늘 할 일, 코딩 공부에서 골랐어요.</div></section>` : ""}
      ${rec.length ? `<section class="day"><div class="dhead"><span class="date">🕒 최근 검색</span><span class="sp"></span><button class="mini-btn" data-act="wclear">지우기</button></div>
      <div class="filters" style="margin:6px 0 0">${rec.map(r => `<button data-act="wgo" data-q="${esc(r)}">${esc(r)}</button>`).join("")}</div></section>` : ""}`}
    <div id="wres"></div>
    <section class="day"><div class="dhead"><span class="date">🌐 ${q ? `"${esc(q)}" 다른 곳에서 찾기` : "검색 사이트"}</span></div>
      ${WEB_SITES.map(g => `<div class="lbl" style="margin-top:8px">${g.g}</div><div class="rbtns" style="margin-top:4px">${g.items.map(([n, u]) =>
        q ? `<a class="mini-btn" href="${esc(webLink(u, q))}" target="_blank" rel="noopener noreferrer">${n}</a>` : `<button class="mini-btn" data-act="wsite" data-u="${esc(u)}">${n}</button>`).join("")}</div>`).join("")}
      <div class="empty" style="font-size:12px">${q ? "누르면 그 사이트의 검색 결과가 새 창으로 열려요." : "위에 검색어를 쓰고 사이트를 누르면 그 사이트에서 바로 찾아 줘요."}</div></section>`;
  $("wform").onsubmit = e => { e.preventDefault(); webSearch($("wq").value); };
  $("wq").oninput = e => { webQuery = e.target.value; if (!e.target.value.trim() && webRes) { webRes = null; renderWeb(); $("wq").focus(); } };
  webList();
}
function webList() {
  const box = $("wres"); if (!box) return;
  const q = webQuery.trim(); if (!q) { box.innerHTML = ""; return; }
  if (webBusy) { box.innerHTML = `<section class="day"><div class="loading" style="padding:16px 0">"${esc(q)}" 찾는 중…</div></section>`; return; }
  const r = webRes || {}, sum = r.summary, wiki = r.wiki || [], news = r.news || [];
  box.innerHTML = `${sum ? `<section class="day wsum">${sum.img ? `<img src="${esc(safeUrl(sum.img))}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ""}
      <div class="dhead"><span class="date">📖 ${esc(sum.title)}</span></div>
      ${sum.desc ? `<div class="empty" style="margin:0 0 4px">${esc(sum.desc)}</div>` : ""}
      <div class="lbody">${esc(sum.extract)}</div>
      <a class="mini-btn" style="margin-top:8px" href="${esc(safeUrl(sum.url))}" target="_blank" rel="noopener noreferrer">위키백과에서 더 보기 ›</a></section>` : ""}
    <section class="day"><div class="dhead"><span class="date">🔎 위키백과 검색 결과</span><span class="sp"></span><span class="empty" style="margin:0">${r.total ? `${r.total.toLocaleString()}개` : ""}</span></div>
      ${r.err ? `<div class="err">${esc(r.err)}</div>` : wiki.length ? `<div class="nlist">${wiki.map(w => `<a href="${esc(safeUrl("https://ko.wikipedia.org/wiki/" + encodeURIComponent(w.title.replace(/ /g, "_"))))}" target="_blank" rel="noopener noreferrer"><b>${esc(w.title)}</b><span>${esc(w.snippet)}…</span></a>`).join("")}</div>`
        : `<div class="empty">위키백과에는 딱 맞는 글이 없어요. 아래 사이트에서 찾아보세요.</div>`}</section>
    ${news.length ? `<section class="day"><div class="dhead"><span class="date">📰 앱에 모은 뉴스</span></div>
      <div class="nlist">${news.map(n => `<a href="${esc(safeUrl(n.link))}" target="_blank" rel="noopener noreferrer"><b>${esc(n.title)}</b><span>${esc([n.source, n.time && String(n.time).slice(0, 10)].filter(Boolean).join(" · "))}</span></a>`).join("")}</div></section>` : ""}`;
}
async function webSearch(raw) {
  const q = String(raw || "").replace(/\s+/g, " ").trim().slice(0, 100);
  webQuery = q; webRes = null;
  if (!q) return renderWeb();
  store("wrecent", JSON.stringify([q, ...webRecent().filter(x => x !== q)].slice(0, 10)));
  const seq = ++webSeq; webBusy = true; renderWeb();
  const api = "https://ko.wikipedia.org/w/api.php?action=query&list=search&format=json&origin=*&srlimit=8&srsearch=" + encodeURIComponent(q);
  const res = { wiki: [], news: [] };
  try {
    const [s] = await Promise.all([fetch(api).then(r => r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status))), fetchNews()]);
    res.wiki = ((s.query && s.query.search) || []).map(x => ({ title: String(x.title), snippet: stripTags(x.snippet) }));
    res.total = (s.query && s.query.searchinfo && s.query.searchinfo.totalhits) || 0;
    const top = res.wiki[0];
    if (top) {
      const p = await fetch("https://ko.wikipedia.org/api/rest_v1/page/summary/" + encodeURIComponent(top.title.replace(/ /g, "_"))).then(r => r.ok ? r.json() : null).catch(() => null);
      if (p && p.extract && p.type !== "disambiguation") res.summary = { title: p.title || top.title, desc: p.description || "", extract: p.extract,
        img: p.thumbnail && p.thumbnail.source, url: (p.content_urls && p.content_urls.mobile && p.content_urls.mobile.page) || "" };
    }
  } catch (e) { res.err = "인터넷 검색을 못 했어요 (연결을 확인해 주세요). 아래 사이트 버튼으로 찾아볼 수 있어요."; }
  const words = q.toLowerCase().split(" ").filter(Boolean);
  for (const c of newsCats()) for (const n of c.items || [])
    if (res.news.length < 6 && words.every(w => String(n.title || "").toLowerCase().includes(w)) && !res.news.some(x => x.link === n.link)) res.news.push(n);
  if (seq !== webSeq) return;
  webBusy = false; webRes = res;
  if (mode === "web" && $("wres")) webList();
}
function webClick(b) {
  const act = b.dataset.act;
  if (act === "wgo") return webSearch(b.dataset.q);
  if (act === "wclear") { store("wrecent", null); return renderWeb(); }
  if (act === "wsite") {
    const q = ($("wq") && $("wq").value.trim()) || "";
    if (!q) { toast("먼저 찾을 것을 써 주세요"); $("wq") && $("wq").focus(); return; }
    window.open(webLink(b.dataset.u, q), "_blank", "noopener,noreferrer");
  }
}

/* ---------- 코딩 공부 (강의: docs/learn.json, 내 진도·코드: Supabase learn.json) ---------- */
const LEARN_PATH = "learn.json";
let learnData = null, learnLang = store("llang") || "py", learnOpen = null, learnShow = {}, learnOut = null, learnRunning = false;
let learnProg = { done: {}, code: {}, stdin: {} };
async function loadLearn(seq = loadSeq) {
  $("label").innerHTML = `코딩 공부<span class="sub">파이썬 · C · 자바스크립트 · HTML · CSS</span>`;
  $("view").innerHTML = `<div class="loading">불러오는 중…</div>`;
  try {
    const [r, f] = await Promise.all([fetch("learn.json?v=" + Date.now(), { cache: "no-store" }), SB ? getFile(LEARN_PATH) : null]);
    learnData = await r.json();
    let p = null; try { p = JSON.parse(SB ? (f ? f.text : "null") : store("learn")); } catch (e) {}
    learnProg = { done: {}, code: {}, stdin: {}, ...(p || {}) };
    if (seq === loadSeq) renderLearn();
  } catch (e) { if (seq === loadSeq) showError(e); }
}
async function saveLearn() {
  const text = JSON.stringify(learnProg);
  try { if (SB) await updateFile(LEARN_PATH, () => text, "코딩 공부 진도"); else store("learn", text); }
  catch (e) { toast("진도를 저장하지 못했어요"); }
}
const lid = (k, i) => `${k}-${i + 1}`;
const curLang = () => learnData.langs.find(l => l.key === learnLang);
function mdLite(src) {
  const inl = t => esc(t).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
  return src.split(/\n\s*\n/).map(blk => {
    const ls = blk.split("\n").map(l => l.trim()).filter(Boolean);
    if (ls.every(l => l.startsWith("- "))) return `<ul>${ls.map(l => `<li>${inl(l.slice(2))}</li>`).join("")}</ul>`;
    if (ls.every(l => l.startsWith("|"))) return `<table>${ls.filter(l => !/^\|[\s|:-]+\|$/.test(l)).map((l, i) =>
      `<tr>${l.replace(/^\||\|$/g, "").split("|").map(c => i ? `<td>${inl(c.trim())}</td>` : `<th>${inl(c.trim())}</th>`).join("")}</tr>`).join("")}</table>`;
    return `<p>${ls.map(inl).join("<br>")}</p>`;
  }).join("");
}
function renderLearn() {
  const d = learnData;
  const bar = `<div class="kindbar nkinds">${d.langs.map(l => `<button data-act="Llang" data-k="${l.key}" class="${l.key === learnLang ? "on" : ""}">${esc(l.name)}</button>`).join("")}
    <button data-act="Llang" data-k="more" class="${learnLang === "more" ? "on" : ""}">📚 더 배우기</button></div>`;
  if (learnLang === "more") {
    $("view").innerHTML = bar + d.links.map(g => `<section class="day"><div class="dhead"><span class="date">${esc(g.name)}</span></div>
      <div class="nlist">${g.items.map(x => `<a href="${esc(safeUrl(x.u))}" target="_blank" rel="noopener noreferrer"><b>${esc(x.t)}</b><span>${esc(x.u.replace(/^https?:\/\//, "").replace(/\/.*$/, ""))}</span></a>`).join("")}</div></section>`).join("");
    return;
  }
  const L = curLang() || d.langs[0]; learnLang = L.key;
  const nDone = L.lessons.filter((_, i) => learnProg.done[lid(L.key, i)]).length;
  if (learnOpen == null) {
    $("view").innerHTML = bar + `<section class="day"><div class="dhead"><span class="date">${esc(L.name)}</span><span class="sp"></span><span class="empty" style="margin:0">${nDone}/${L.lessons.length} 완료</span></div>
      <div class="lbody">${mdLite(L.intro)}</div><div class="lbar"><i style="width:${Math.round(nDone / L.lessons.length * 100)}%"></i></div>
      <div class="llist">${L.lessons.map((x, i) => `<button data-act="Lopen" data-i="${i}"><span class="n ${learnProg.done[lid(L.key, i)] ? "ok" : ""}">${learnProg.done[lid(L.key, i)] ? "✓" : i + 1}</span><span>${esc(x.t)}</span></button>`).join("")}</div></section>`;
    return;
  }
  const i = learnOpen, x = L.lessons[i], id = lid(L.key, i), html = L.run === "html";
  const code = learnProg.code[id] ?? x.code, stdin = learnProg.stdin[id] ?? (x.stdin || "");
  $("view").innerHTML = bar + `<section class="day">
    <div class="dhead"><button class="mini-btn" data-act="Lback">← 목록</button><span class="sp"></span><span class="empty" style="margin:0">${esc(L.name)} ${i + 1}/${L.lessons.length}</span></div>
    <h3 style="margin:8px 0 4px">${learnProg.done[id] ? "✅ " : ""}${esc(x.t)}</h3>
    <div class="lbody">${mdLite(x.b)}</div>
    <label style="margin-top:10px">✏️ 코드 <span class="hint">— 마음대로 고쳐 보세요</span></label>
    <textarea class="lcode" id="lcode" spellcheck="false" autocapitalize="off" autocomplete="off" autocorrect="off">${esc(code)}</textarea>
    ${L.run === "python" || L.run === "c" ? `<label>⌨️ 입력값 <span class="hint">— 프로그램이 읽을 입력, 한 줄에 하나</span></label><textarea class="lstdin" id="lstdin" spellcheck="false" autocapitalize="off">${esc(stdin)}</textarea>` : ""}
    <div class="rbtns"><button class="mini-btn go" data-act="Lrun" ${learnRunning ? "disabled" : ""}>${learnRunning ? "⏳ 실행 중…" : "▶ 실행"}</button>
      <button class="mini-btn" data-act="Lreset">↺ 처음 코드로</button></div>
    ${html ? `<iframe class="lframe" id="lframe" sandbox="allow-scripts allow-modals" title="실행 결과"></iframe>` : `<pre class="lout" id="lout"><span class="m">▶ 실행을 누르면 여기에 결과가 나와요${L.run === "python" ? " (파이썬은 처음 한 번 준비하는 데 10초쯤 걸려요)" : L.run === "c" ? " (C 코드는 실행하려고 Compiler Explorer 서버로 보내요)" : ""}</span></pre>`}
    ${x.task ? `<div class="ltask"><b>🎯 도전 과제</b><div class="lbody">${mdLite(x.task)}</div>
      <div class="rbtns">${x.hint ? `<button class="mini-btn" data-act="Lhint">💡 힌트</button>` : ""}${x.ans ? `<button class="mini-btn" data-act="Lans">👀 정답 보기</button>` : ""}</div>
      ${learnShow.hint && x.hint ? `<div class="lbody" style="margin-top:6px">💡 ${mdLite(x.hint)}</div>` : ""}
      ${learnShow.ans && x.ans ? `<pre class="lout" style="color:#e5e7eb">${esc(x.ans)}</pre><div class="rbtns"><button class="mini-btn" data-act="Luse">이 코드를 에디터에 넣기</button></div>` : ""}
      ${x.expect ? `<div class="empty" style="margin:6px 0 0;font-size:12px">실행 결과가 맞으면 자동으로 완료돼요.</div>` : ""}</div>` : ""}
    <div class="lnav">${i > 0 ? `<button class="mini-btn" data-act="Lgo" data-i="${i - 1}">◀ 이전</button>` : ""}<span class="sp"></span>
      <button class="mini-btn ${learnProg.done[id] ? "" : "go"}" data-act="Ldone">${learnProg.done[id] ? "완료 취소" : "✅ 완료"}</button>
      ${i < L.lessons.length - 1 ? `<button class="mini-btn" data-act="Lgo" data-i="${i + 1}">다음 ▶</button>` : ""}</div></section>`;
  const ta = $("lcode");
  ta.oninput = () => { learnProg.code[id] = ta.value; };
  ta.onkeydown = e => {
    if (e.key !== "Tab") return;
    e.preventDefault();
    const sp = L.run === "python" || L.run === "c" ? "    " : "  ", a = ta.selectionStart;
    ta.setRangeText(sp, a, ta.selectionEnd, "end"); learnProg.code[id] = ta.value;
  };
  if ($("lstdin")) $("lstdin").oninput = e => { learnProg.stdin[id] = e.target.value; };
  if (learnOut) showLearnOut(learnOut);
}
function showLearnOut(r) {
  const el = $("lout"); if (!el) return;
  el.innerHTML = (r.out ? esc(r.out) : "") + (r.err ? `${r.out ? "\n" : ""}<span class="e">${esc(r.err)}</span>` : "")
    + (!r.out && !r.err ? `<span class="m">(출력 없음)</span>` : "") + (r.ok ? `\n<span class="m">🎉 도전 과제 성공!</span>` : "");
}
const outMatch = (out, e) => out.split("\n").some(l => l.trim() === e) || (e.length >= 4 && out.includes(e));
async function learnClick(b) {
  const act = b.dataset.act, L = curLang();
  const go = i => { learnOpen = i; learnShow = {}; learnOut = null; renderLearn(); window.scrollTo({ top: 0 }); };
  if (act === "Llang") { learnLang = b.dataset.k; store("llang", learnLang); learnOpen = null; learnOut = null; return renderLearn(); }
  if (act === "Lopen" || act === "Lgo") return go(+b.dataset.i);
  if (act === "Lback") { learnOpen = null; saveLearn(); return renderLearn(); }
  const i = learnOpen, x = L.lessons[i], id = lid(L.key, i);
  if (act === "Lhint") { learnShow.hint = !learnShow.hint; return renderLearn(); }
  if (act === "Lans") { learnShow.ans = !learnShow.ans; return renderLearn(); }
  if (act === "Luse") { learnProg.code[id] = x.ans; if (x.astdin) learnProg.stdin[id] = x.astdin; learnOut = null; return renderLearn(); }
  if (act === "Lreset") { delete learnProg.code[id]; delete learnProg.stdin[id]; learnOut = null; renderLearn(); return saveLearn(); }
  if (act === "Ldone") { learnProg.done[id] = !learnProg.done[id]; if (!learnProg.done[id]) delete learnProg.done[id]; else toast("완료 ✓"); renderLearn(); return saveLearn(); }
  if (act === "Lrun") {
    const code = $("lcode").value, stdin = $("lstdin") ? $("lstdin").value : "";
    if (L.run === "html") { runHtml($("lframe"), code); saveLearn(); return; }
    learnRunning = true; learnOut = { out: "", err: "", wait: true };
    renderLearn(); $("lout").innerHTML = `<span class="m">⏳ ${L.run === "python" && !pyReady ? "파이썬 준비 중… (처음 한 번만 10초쯤)" : "실행 중…"}</span>`;
    let r;
    try { r = L.run === "python" ? await runPython(code, stdin) : L.run === "c" ? await runC(code, stdin) : await runJS(code); }
    catch (e) { r = { out: "", err: e.message || String(e) }; }
    learnRunning = false;
    if (x.expect && !r.err && outMatch(r.out || "", x.expect) && !learnProg.done[id]) { learnProg.done[id] = true; r.ok = true; }
    learnOut = r;
    if (mode === "learn" && curLang() === L && learnOpen === i) renderLearn();
    saveLearn();
  }
}
// HTML·CSS: sandbox.html 을 새로 열고 코드를 보내요 (주인 없는 출처라 앱의 로그인 정보에 못 닿아요)
function runHtml(f, code) {
  f.onload = () => { f.onload = null; f.contentWindow.postMessage({ html: code }, "*"); };
  f.src = "sandbox.html?" + Date.now();   // 실행할 때마다 깨끗한 새 페이지
}
// 자바스크립트: 웹 워커에서 실행 (무한 반복이어도 앱이 멈추지 않게 5초 뒤 끊어요)
function jsWorkerMain() {
  const fmt = (v, d) => typeof v === "string" ? (d ? "'" + v + "'" : v)
    : Array.isArray(v) ? (v.length ? "[ " + v.map(x => fmt(x, 1)).join(", ") + " ]" : "[]")
    : v && typeof v === "object" ? (Object.keys(v).length ? "{ " + Object.keys(v).map(k => k + ": " + fmt(v[k], 1)).join(", ") + " }" : "{}")
    : typeof v === "function" ? "[Function]" : String(v);
  const out = [];
  console.log = console.info = console.warn = console.error = (...a) => out.push(a.map(x => fmt(x, 0)).join(" "));
  onmessage = e => {
    try { (0, eval)(e.data); postMessage({ out: out.join("\n") }); }
    catch (err) { postMessage({ out: out.join("\n"), err: (err && err.name ? err.name + ": " + err.message : String(err)) }); }
  };
}
const workerOf = fn => new Worker(URL.createObjectURL(new Blob([`(${fn.toString()})()`], { type: "text/javascript" })));
function runJS(code) {
  return new Promise(ok => {
    const w = workerOf(jsWorkerMain);
    const t = setTimeout(() => { w.terminate(); ok({ out: "", err: "⏱ 5초가 넘어서 멈췄어요. 끝나지 않는 반복이 있는지 확인해 보세요." }); }, 5000);
    w.onmessage = e => { clearTimeout(t); w.terminate(); ok(e.data); };
    w.onerror = e => { clearTimeout(t); w.terminate(); ok({ out: "", err: e.message || "오류" }); e.preventDefault(); };
    w.postMessage(code);
  });
}
// 파이썬: Pyodide(브라우저용 파이썬)를 웹 워커에서 실행
let pyW = null, pyReady = false, pyWait = null;
function pyWorkerMain() {
  importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js");
  const ready = loadPyodide().then(p => { postMessage({ ready: true }); return p; }, e => { postMessage({ fail: String(e) }); throw e; });
  onmessage = async e => {
    const py = await ready, out = [];
    py.setStdout({ batched: s => out.push(s) });
    py.setStderr({ batched: s => out.push(s) });
    const lines = e.data.stdin ? e.data.stdin.split("\n") : []; let i = 0;
    py.setStdin({ stdin: () => i < lines.length ? lines[i++] : undefined });
    try { await py.runPythonAsync(e.data.code); postMessage({ out: out.join("\n") }); }
    catch (err) {
      const m = String(err && err.message || err).trim().split("\n");
      const at = m.filter(l => /File "<exec>", line \d+/.test(l)).pop();
      const ln = at && at.match(/line (\d+)/)[1];
      postMessage({ out: out.join("\n"), err: (ln ? ln + "번째 줄 → " : "") + m[m.length - 1] });
    }
  };
}
function pyStart() {
  pyW = workerOf(pyWorkerMain); pyReady = false;
  pyW.onmessage = e => {
    if (e.data.ready) { pyReady = true; return; }
    if (e.data.fail) { const w = pyWait; pyWait = null; pyW.terminate(); pyW = null; if (w) w({ out: "", err: "파이썬을 불러오지 못했어요. 인터넷 연결을 확인해 주세요." }); return; }
    const w = pyWait; pyWait = null; if (w) w(e.data);
  };
}
function runPython(code, stdin) {
  if (!pyW) pyStart();
  return new Promise(ok => {
    const started = Date.now(); let runFrom = pyReady ? started : null;
    const tick = setInterval(() => {   // 준비가 90초, 실행이 10초를 넘으면 멈추고 다음에 새로 시작
      if (pyReady && !runFrom) runFrom = Date.now();
      const late = runFrom ? Date.now() - runFrom > 10000 : Date.now() - started > 90000;
      if (!late) return;
      clearInterval(tick); if (pyW) pyW.terminate(); pyW = null; pyWait = null;
      ok({ out: "", err: runFrom ? "⏱ 10초가 넘어서 멈췄어요. 끝나지 않는 반복이 있는지 확인해 보세요." : "⏱ 파이썬 준비가 너무 오래 걸려요. 인터넷 연결을 확인하고 다시 실행해 주세요." });
      pyReady = false;
    }, 300);
    pyWait = r => { clearInterval(tick); ok(r); };
    pyW.postMessage({ code, stdin });
  });
}
// C: Compiler Explorer(godbolt.org)의 gcc 로 컴파일·실행
async function runC(code, stdin) {
  const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), 30000);
  try {
    const r = await fetch("https://godbolt.org/api/compiler/cg132/compile", { method: "POST", signal: ctl.signal,
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({ source: code, lang: "c", allowStoreCodeDebug: false,
        options: { userArguments: "-O1 -std=c11", executeParameters: { args: [], stdin },
          compilerOptions: { executorRequest: true, skipAsm: true }, filters: { execute: true }, tools: [], libraries: [] } }) });
    if (!r.ok) throw new Error(`실행 서버 오류 (${r.status})`);
    const j = await r.json();
    const txt = a => (a || []).map(x => x.text).join("\n").replace(/\x1b\[[0-9;]*[mK]/g, "").replace(/<source>/g, "코드");
    const b = j.buildResult || {};
    if ((b.code || 0) !== 0 || j.didExecute === false) return { out: "", err: "🔨 컴파일 오류\n" + (txt(b.stderr) || txt(j.stderr) || "컴파일하지 못했어요") };
    const out = txt(j.stdout), er = txt(j.stderr);
    return { out, err: j.timedOut ? "⏱ 시간이 너무 오래 걸려서 멈췄어요." : (er || (j.code ? `프로그램이 오류 코드 ${j.code} 로 끝났어요` : "")) };
  } catch (e) {
    return { out: "", err: e.name === "AbortError" ? "⏱ 실행 서버가 응답하지 않아요. 잠시 뒤 다시 해 주세요." : "C 실행 서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요. (" + e.message + ")" };
  } finally { clearTimeout(t); }
}

/* ---------- 지도 (장소는 Supabase 내 계정에 저장, places.json) ---------- */
const PLACE_PATH = "places.json";
const localPlaces = () => { try { const a = JSON.parse(store("places") || "[]"); return Array.isArray(a) ? a : []; } catch (e) { return []; } };
let places = SB ? [] : localPlaces();
let placeDraft = null, lmap = null, lmarkers = [], draftMarker = null, myPos = null, routeFrom = "me", routeTo = "";
const parsePlaces = text => { try { const j = text ? JSON.parse(text) : {}; return Array.isArray(j.places) ? j.places : []; } catch (e) { return []; } };
async function loadPlaces(force) {
  if (!SB) { places = localPlaces(); return; }   // 예전 GitHub(공개 저장소) 방식일 땐 이 기기에만
  places = parsePlaces((await getFile(PLACE_PATH, force) || {}).text);
  const old = localPlaces();   // 예전에 이 기기에만 저장해 둔 장소 → 내 계정으로 한 번 옮기기
  if (old.length) {
    await writePlaces(list => [...list, ...old.filter(o => !list.some(x => x.id === o.id))]);
    store("places", null); toast(`이 기기에 있던 장소 ${old.length}곳을 계정으로 옮겼어요`);
  }
}
// fn(현재 목록) -> 새 목록. Supabase 에서는 최신본 위에 고쳐서 저장
async function writePlaces(fn) {
  if (!SB) { places = fn(localPlaces()); store("places", JSON.stringify(places)); return; }
  await updateFile(PLACE_PATH, text => JSON.stringify({ places: fn(parsePlaces(text)) }, null, 2) + "\n", "앱에서 장소 저장");
  places = parsePlaces(files.get(PLACE_PATH).text);
}
/* 지도 엔진: docs/config.js 에 kakaoJsKey 가 있으면 카카오맵, 없거나 못 불러오면 OpenStreetMap(Leaflet) */
let kakaoOn = false;
const addScript = (src, ms, integrity) => new Promise((ok, bad) => {
  const sc = document.createElement("script"); sc.src = src; sc.onload = ok; sc.onerror = () => bad(new Error("load"));
  if (integrity) { sc.integrity = integrity; sc.crossOrigin = "anonymous"; }   // 🔒 CDN 파일이 바꿔치기되면 실행 안 함
  if (ms) setTimeout(() => bad(new Error("timeout")), ms);
  document.head.appendChild(sc);
});
async function loadKakao() {
  if (window.kakao && kakao.maps && kakao.maps.services) return;
  await addScript(`https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(CFG.kakaoJsKey)}&libraries=services&autoload=false`, 8000);
  await new Promise((ok, bad) => { setTimeout(() => bad(new Error("timeout")), 8000); kakao.maps.load(ok); });
}
async function loadMapLib() {
  if (CFG.kakaoJsKey) {
    try { await loadKakao(); kakaoOn = true; return; }
    catch (e) { console.warn("카카오맵을 못 불러와서 OpenStreetMap 으로 보여요", e); kakaoOn = false; }
  }
  if (window.L) return;
  try { await addScript("https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js", 0, "sha384-cxOPjt7s7Iz04uaHJceBmS+qpjv2JkIHNVcuOrM+YHwZOmJGBXI00mdUXEq65HTH"); }
  catch (e) { throw new Error("지도를 불러오지 못했어요. 인터넷 연결을 확인해 주세요."); }
}
async function loadMap(seq = loadSeq) {
  $("label").innerHTML = `지도<span class="sub">자주 가는 곳 · 길찾기</span>`;
  $("view").innerHTML = `<div class="loading">지도 불러오는 중…</div>`;
  try { await Promise.all([loadMapLib(), loadPlaces()]); if (seq === loadSeq) renderMap(); } catch (e) { if (seq === loadSeq) showError(e); }
}
const placeOpts = sel => [`<option value="me" ${sel === "me" ? "selected" : ""}>📍 현재 위치</option>`,
  ...places.map(p => `<option value="${p.id}" ${sel === p.id ? "selected" : ""}>${esc(p.icon || "📌")} ${esc(p.name)}</option>`)].join("");
function renderMap() {
  const d = placeDraft;
  $("view").innerHTML = `<div id="map"></div>
    ${d ? `<section class="day editing rform">
        <div class="dhead"><span class="date">${d.id ? "✏️ 장소 수정" : "📌 새 장소"}</span></div>
        <label>이름</label><input data-q="name" value="${esc(d.name)}" placeholder="예) 집, 학교, 수학 학원">
        <label>아이콘</label><input data-q="icon" value="${esc(d.icon || "📌")}" maxlength="4" style="width:80px">
        <label>위치 찾기 <span class="hint">— 검색하거나, 지도를 눌러 핀을 옮기거나, 현재 위치</span></label>
        <div style="display:flex;gap:6px"><input id="qsearch" placeholder="예) ○○고등학교, ○○역" style="flex:1"><button class="btn" data-act="qfind">검색</button></div>
        <div class="sres" id="sres"></div>
        <div class="rbtns"><button class="mini-btn" data-act="qhere">📍 현재 위치로</button>
          <span class="empty" style="margin:0;align-self:center">${d.lat ? `핀: ${(+d.lat).toFixed(5)}, ${(+d.lng).toFixed(5)}` : "아직 위치를 안 정했어요"}</span></div>
        <label>메모</label><input data-q="memo" value="${esc(d.memo || "")}" placeholder="예) 2번 출구, 302번 버스">
        <div class="actions" style="margin-top:12px">
          ${d.id ? `<button class="btn ghost danger" data-act="qdel" style="margin-right:auto">🗑 삭제</button>` : ""}
          <button class="btn ghost" data-act="qcancel" ${saving ? "disabled" : ""}>취소</button><button class="btn" data-act="qsave" ${saving ? "disabled" : ""}>${saving ? "저장 중…" : "저장"}</button></div></section>`
    : `<section class="day"><div class="dhead"><span class="date">🚌 길찾기</span></div>
        <div class="route"><select id="rfrom">${placeOpts(routeFrom)}</select><span>→</span><select id="rto"><option value="">도착지</option>${places.map(p => `<option value="${p.id}" ${routeTo === p.id ? "selected" : ""}>${esc(p.icon || "📌")} ${esc(p.name)}</option>`).join("")}</select></div>
        <div class="rbtns"><button class="mini-btn go" data-act="qroute" data-m="traffic">🚌 대중교통</button><button class="mini-btn" data-act="qroute" data-m="walk">🚶 도보</button>
          <button class="mini-btn" data-act="qroute" data-m="car">🚗 자동차</button><button class="mini-btn" data-act="qroute" data-m="naver">🟢 네이버 지도</button>
          <button class="mini-btn" data-act="qroute" data-m="google">🔵 구글 지도</button></div>
        <div class="empty">카카오맵·네이버 지도·구글 지도에서 경로·버스 도착 정보가 열려요. (구글 지도는 우리나라에서 대중교통 길찾기만 돼요)</div>
</section>
      <section class="day"><div class="dhead"><span class="date">⭐ 자주 가는 곳</span><span class="sp"></span><button class="mini-btn go" data-act="qnew">+ 장소 추가</button></div>
        ${places.length ? `<div class="plist">${places.map(p => `<div class="pl" data-id="${p.id}"><span style="font-size:20px">${esc(p.icon || "📌")}</span>
          <div class="pn"><b>${esc(p.name)}</b>${p.memo ? `<span>${esc(p.memo)}</span>` : ""}</div>
          <button class="mini-btn go" data-act="qto">🚌 가기</button><button class="pencil" data-act="qedit" aria-label="수정">✏️</button></div>`).join("")}</div>`
          : '<div class="empty">집, 학교, 학원처럼 자주 가는 곳을 저장해 보세요.</div>'}
        <div class="empty" style="font-size:12px">🔒 ${SB ? "장소는 내 계정(Supabase)에만 저장돼서 로그인한 기기 어디서나 보여요." : "장소는 GitHub(공개 저장소)이 아니라 이 휴대폰에만 저장돼요."}</div></section>`}`;
  drawMap();
  const rf = $("rfrom"), rt = $("rto");
  if (rf) rf.onchange = () => routeFrom = rf.value;
  if (rt) rt.onchange = () => routeTo = rt.value;
}
const pinHtml = (icon, name) => `<div class="pinb"><span>${esc(icon || "📌")}</span></div><div class="pinl">${esc(name || "")}</div>`;
// 핀 하나 만들기 → { move(lat, lng) }
function addPin(lat, lng, icon, name) {
  if (kakaoOn) {
    const el = document.createElement("div"); el.className = "pin kpin"; el.innerHTML = pinHtml(icon, name);
    const o = new kakao.maps.CustomOverlay({ map: lmap, position: new kakao.maps.LatLng(lat, lng), content: el, xAnchor: 0.5, yAnchor: 1.05, zIndex: 3 });
    return { move: (a, b) => o.setPosition(new kakao.maps.LatLng(a, b)) };
  }
  const m = L.marker([lat, lng], { icon: L.divIcon({ className: "pin", iconSize: null, iconAnchor: [14, 30], html: pinHtml(icon, name) }) }).addTo(lmap);
  return { move: (a, b) => m.setLatLng([a, b]) };
}
function mapFocus(lat, lng) {   // 그 자리로 가까이
  if (kakaoOn) { lmap.setCenter(new kakao.maps.LatLng(lat, lng)); if (lmap.getLevel() > 3) lmap.setLevel(3); }
  else lmap.setView([lat, lng], Math.max(lmap.getZoom(), 16), { animate: false });
}
function drawMap() {
  if (lmap && !kakaoOn && lmap.remove) { lmap.stop(); lmap.off(); lmap.remove(); }
  lmap = null; draftMarker = null;
  const pts = [...places.filter(p => p.lat).map(p => [p.lat, p.lng]), ...(placeDraft && placeDraft.lat ? [[placeDraft.lat, placeDraft.lng]] : [])];
  const home = pts[0] || [37.2636, 127.0286];   // 기본: 경기 남부
  if (kakaoOn) {
    lmap = new kakao.maps.Map($("map"), { center: new kakao.maps.LatLng(home[0], home[1]), level: pts.length ? 3 : 7 });
    lmap.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
    if (placeDraft) kakao.maps.event.addListener(lmap, "click", e => setDraftPos(e.latLng.getLat(), e.latLng.getLng()));
    if (pts.length > 1) {
      const bd = new kakao.maps.LatLngBounds(); pts.forEach(p => bd.extend(new kakao.maps.LatLng(p[0], p[1])));
      lmap.setBounds(bd, 45, 45, 45, 45); if (lmap.getLevel() < 3) lmap.setLevel(3);
    }
  } else {
    lmap = L.map("map", { zoomControl: true, attributionControl: true, zoomAnimation: false, fadeAnimation: false, markerZoomAnimation: false });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "© OpenStreetMap" }).addTo(lmap);
    if (placeDraft) lmap.on("click", e => setDraftPos(e.latlng.lat, e.latlng.lng));
    if (pts.length > 1) lmap.fitBounds(pts, { padding: [45, 45], maxZoom: 16, animate: false });
    else lmap.setView(home, pts.length ? 16 : 12);
  }
  lmarkers = places.filter(p => p.lat).map(p => addPin(p.lat, p.lng, p.icon, p.name));
  if (placeDraft && placeDraft.lat) draftMarker = addPin(placeDraft.lat, placeDraft.lng, "📍", "여기");
}
function setDraftPos(lat, lng) {
  placeDraft.lat = +lat; placeDraft.lng = +lng;
  if (draftMarker) draftMarker.move(+lat, +lng); else draftMarker = addPin(+lat, +lng, "📍", "여기");
  mapFocus(+lat, +lng);
  const info = document.querySelector(".rbtns .empty"); if (info) info.textContent = `핀: ${(+lat).toFixed(5)}, ${(+lng).toFixed(5)}`;
}
// 장소 검색 → [{ name, addr, lat, lng }]. 카카오맵이면 카카오 장소 검색(가게·학원·역 이름도 잘 찾음)
function searchPlaces(q) {
  if (kakaoOn) return new Promise((ok, bad) => new kakao.maps.services.Places().keywordSearch(q, (data, st) => {
    if (st === kakao.maps.services.Status.ZERO_RESULT) return ok([]);
    if (st !== kakao.maps.services.Status.OK) return bad(new Error(st));
    ok(data.map(x => ({ name: x.place_name, addr: x.road_address_name || x.address_name, lat: +x.y, lng: +x.x })));
  }, { location: lmap.getCenter(), size: 8 }));
  const c = lmap.getCenter();
  return fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=6&accept-language=ko&countrycodes=kr&q=${encodeURIComponent(q)}&viewbox=${c.lng - 0.5},${c.lat + 0.5},${c.lng + 0.5},${c.lat - 0.5}`)
    .then(r => r.json()).then(j => j.map(x => ({ name: x.display_name, addr: "", lat: +x.lat, lng: +x.lon })));
}
function getPos() {
  return new Promise((ok, bad) => {
    if (!navigator.geolocation) return bad(new Error("이 기기에서는 위치를 쓸 수 없어요"));
    navigator.geolocation.getCurrentPosition(p => { myPos = { lat: p.coords.latitude, lng: p.coords.longitude }; ok(myPos); },
      () => bad(new Error("위치 권한을 허용해 주세요")), { enableHighAccuracy: true, timeout: 10000 });
  });
}
const enc = s => encodeURIComponent(String(s).replace(/,/g, " "));
async function placeClick(b) {
  const act = b.dataset.act;
  if (act === "qnew") { placeDraft = { name: "", icon: "📌", memo: "", lat: null, lng: null }; return renderMap(); }
  if (act === "qedit") { placeDraft = structuredClone(places.find(p => p.id === b.closest("[data-id]").dataset.id)); return renderMap(); }
  if (act === "qcancel") { placeDraft = null; draftMarker = null; return renderMap(); }
  if (act === "qhere") { try { const p = await getPos(); setDraftPos(p.lat, p.lng); } catch (e) { toast(e.message); } return; }
  if (act === "qfind") {
    const q = $("qsearch").value.trim(); if (!q) return;
    $("sres").innerHTML = '<div class="empty">찾는 중…</div>';
    try {
      const j = await searchPlaces(q);
      $("sres").innerHTML = j.length ? j.map(x => `<button data-act="qpick" data-lat="${esc(x.lat)}" data-lng="${esc(x.lng)}" data-name="${esc(x.name)}"><b>${esc(x.name)}</b>${x.addr ? `<br><span class="hint">${esc(x.addr)}</span>` : ""}</button>`).join("")
        : '<div class="empty">못 찾았어요. 다른 이름으로 검색하거나 지도를 눌러 핀을 찍어 주세요.</div>';
    } catch (e) { $("sres").innerHTML = '<div class="empty">검색이 안 돼요. 지도를 눌러 핀을 찍어 주세요.</div>'; }
    return;
  }
  if (act === "qpick") {
    setDraftPos(b.dataset.lat, b.dataset.lng); $("sres").innerHTML = "";
    if (kakaoOn && !(placeDraft.name || "").trim() && b.dataset.name) { placeDraft.name = b.dataset.name; const n = document.querySelector('[data-q="name"]'); if (n) n.value = b.dataset.name; }
    return;
  }
  if (act === "qsave") {
    const d = placeDraft;
    if (!(d.name || "").trim()) return toast("이름을 적어 주세요");
    if (!d.lat) return toast("위치를 정해 주세요 (검색 · 지도 누르기 · 현재 위치)");
    const p = { id: d.id || "p" + Date.now().toString(36), name: d.name.trim(), icon: (d.icon || "📌").trim(), memo: (d.memo || "").trim(), lat: +d.lat, lng: +d.lng };
    return savePlace(list => [...list.filter(x => x.id !== p.id), p], "장소 저장됨 ✓");
  }
  if (act === "qdel") { if (!confirm(`'${placeDraft.name}' 장소를 지울까요?`)) return; const id = placeDraft.id; return savePlace(list => list.filter(x => x.id !== id), "지웠어요"); }
  if (act === "qto") { routeTo = b.closest("[data-id]").dataset.id; return openRoute("traffic"); }
  if (act === "qroute") return openRoute(b.dataset.m);
}
async function savePlace(fn, msg) {
  saving = true; renderMap();
  try { await writePlaces(fn); }
  catch (e) { saving = false; renderMap(); showError(e, true); return; }
  saving = false; placeDraft = null; draftMarker = null; toast(msg); renderMap();
}
async function routeEnds() {
  const to = places.find(p => p.id === (routeTo || ($("rto") && $("rto").value)));
  if (!to) { toast("도착지를 골라 주세요"); return null; }
  let from = routeFrom === "me" ? null : places.find(p => p.id === routeFrom);
  if (!from) { try { const p = await getPos(); from = { name: "현재 위치", ...p }; } catch (e) { from = null; } }
  return { from, to };
}
const ll = p => `${p.lat},${p.lng}`;
async function openRoute(m) {
  const r = await routeEnds(); if (!r) return;
  const { from, to } = r;
  let url;
  if (m === "google") {   // 우리나라는 구글 길찾기가 대중교통만 지원
    const q = new URLSearchParams({ api: "1", destination: ll(to), travelmode: "transit" });
    if (from) q.set("origin", ll(from));
    url = "https://www.google.com/maps/dir/?" + q;
  } else if (m === "naver") url = from
    ? `https://map.naver.com/p/directions/${from.lng},${from.lat},${enc(from.name)},,/${to.lng},${to.lat},${enc(to.name)},,/-/transit`
    : `https://map.naver.com/p/search/${enc(to.name)}`;
  else url = from
    ? `https://map.kakao.com/link/by/${m}/${enc(from.name)},${from.lat},${from.lng}/${enc(to.name)},${to.lat},${to.lng}`
    : `https://map.kakao.com/link/to/${enc(to.name)},${to.lat},${to.lng}`;
  window.open(url, "_blank", "noopener");
}

/* ---------- 이동 ---------- */
function move(dir) {
  if (!leaveOk()) return;
  if (mode === "year") anchor = `${+anchor.slice(0, 4) + dir}-01-01`;
  else if (mode === "report" || mode === "today") anchor = addDays(anchor, dir);
  else if (mode === "week") anchor = addDays(weekStart(anchor), 7 * dir);
  else { const [y, m] = anchor.split("-").map(Number); anchor = iso(new Date(Date.UTC(y, m - 1 + dir, 1))); }
  load();
}
function goToday() {
  if (!leaveOk()) return;
  anchor = todayKST(); if (mode === "month") selDay = anchor; load();
}
$("goToday").onclick = goToday;
$("prev").onclick = () => move(-1);
$("next").onclick = () => move(1);
const closeMore = () => { $("moreMenu").hidden = true; $("moreBtn").setAttribute("aria-expanded", "false"); };
$("moreBtn").onclick = e => { e.stopPropagation(); const h = !$("moreMenu").hidden; $("moreMenu").hidden = h; $("moreBtn").setAttribute("aria-expanded", String(!h)); };
document.addEventListener("click", e => { if (!e.target.closest("#moreMenu")) closeMore(); });
document.querySelectorAll(".tabs button[data-mode], #moreMenu button").forEach(b => b.onclick = () => {
  closeMore();
  if (b.dataset.mode === mode) return showsToday() ? undefined : goToday();
  if (!leaveOk()) return;
  mode = b.dataset.mode; store("mode", mode); anchor = todayKST(); load();
});
// ↻ : 앱 자체도 최신 버전으로 다시 받기 (캐시 우회), 지금 보던 탭·날짜는 그대로
// 📢 공지: 새 뉴스가 들어오면 빨간 숫자, 누르면 공지 화면
$("noticeBtn").onclick = () => {
  closeMore();
  if (mode === "notice" || !leaveOk()) return;
  mode = "notice"; store("mode", mode); load();
};
fetchNews();
setInterval(() => fetchNews(true), 15 * 6e4);
document.addEventListener("visibilitychange", () => { if (!document.hidden) fetchNews(); });
$("reload").onclick = () => {
  if (!leaveOk()) return;
  const q = mode === "report" && reportKind === "date" ? `report=${anchor}` : mode === "today" ? `day=${anchor}` : "";
  location.replace(location.pathname + "?v=" + Date.now() + (q ? "&" + q : ""));
};

/* ---------- 로그인 · 설정 ---------- */
function showLogin(err) {
  $("view").innerHTML = `<div class="panel" style="text-align:center">
    <h2>📅 내 계획표</h2>
    <p>구글 계정으로 로그인하면 <b>내 계정에서만</b> 내 계획이 보여요.</p>
    <button class="btn" id="gLogin" style="width:100%;padding:14px;font-size:16px">G&nbsp; 구글로 로그인</button>
    ${err ? `<div class="err" style="margin-top:10px">${esc(err)}</div>` : ""}
    <p style="font-size:13px;color:var(--muted)">홈 화면에 추가하면 앱처럼 쓸 수 있어요: 브라우저 메뉴(⋮ 또는 공유 버튼) → <b>홈 화면에 추가</b>.</p></div>`;
  $("gLogin").onclick = async () => {
    const { error } = await SB.auth.signInWithOAuth({ provider: "google", options: { redirectTo: location.origin + location.pathname } });
    if (error) showLogin(error.message);
  };
}
const DEFAULT_SCHEDULE = "{\n  \"_설명\": \"기본 시간표(요일마다 반복). weekday: 0=월 1=화 2=수 3=목 4=금 5=토 6=일. remind_before: 몇 분 전에 알림 (0=정각, []=알림 없음)\",\n  \"timezone_offset_hours\": 9,\n  \"default_remind_before\": [\n    10\n  ],\n  \"weekly\": {\n    \"0\": [\n      {\n        \"title\": \"등교\",\n        \"start\": \"08:30\",\n        \"remind_before\": []\n      },\n      {\n        \"title\": \"하교\",\n        \"start\": \"16:00\",\n        \"remind_before\": [\n          0\n        ]\n      }\n    ],\n    \"1\": [\n      {\n        \"title\": \"등교\",\n        \"start\": \"08:30\",\n        \"remind_before\": []\n      },\n      {\n        \"title\": \"하교\",\n        \"start\": \"16:00\",\n        \"remind_before\": [\n          0\n        ]\n      }\n    ],\n    \"2\": [\n      {\n        \"title\": \"등교\",\n        \"start\": \"08:30\",\n        \"remind_before\": []\n      },\n      {\n        \"title\": \"하교\",\n        \"start\": \"16:00\",\n        \"remind_before\": [\n          0\n        ]\n      }\n    ],\n    \"3\": [\n      {\n        \"title\": \"등교\",\n        \"start\": \"08:30\",\n        \"remind_before\": []\n      },\n      {\n        \"title\": \"하교\",\n        \"start\": \"16:00\",\n        \"remind_before\": [\n          0\n        ]\n      }\n    ],\n    \"4\": [\n      {\n        \"title\": \"등교\",\n        \"start\": \"08:30\",\n        \"remind_before\": []\n      },\n      {\n        \"title\": \"하교\",\n        \"start\": \"16:00\",\n        \"remind_before\": [\n          0\n        ]\n      }\n    ],\n    \"5\": [],\n    \"6\": []\n  },\n  \"school\": {\n    \"school_events\": [\n      \"등교\",\n      \"하교\",\n      \"야자\"\n    ],\n    \"exam_keep_events\": [\n      \"등교\"\n    ],\n    \"period_times\": [],\n    \"timetable\": {},\n    \"off_days\": {},\n    \"exam_days\": {},\n    \"vacations\": [],\n    \"notes\": {}\n  },\n  \"report_reminder\": {\n    \"time\": \"23:30\",\n    \"only_school_days\": false\n  },\n  \"todo_reminders\": {\n    \"daily\": [\n      \"07:30\",\n      \"08:00\",\n      \"21:00\"\n    ],\n    \"weekday\": {},\n    \"commute_at\": \"08:00\",\n    \"remaining_from\": \"21:00\"\n  }\n}\n";   // docs/schedule.example.json 과 같음
/* ---------- 처음: 우리 학교·학년 정하기 → 같은 학교·학년 친구들 출판사가 맞는지 묻기 ---------- */
const tbSkipKey = () => "tbskip2_" + (sbUser ? sbUser.id : "");
async function needSchoolSetup() {
  if (!SB || !sbUser || store(tbSkipKey())) return false;
  try { await loadExamData(); } catch (e) { return false; }
  const t = savedTb(examData);
  if (!(t && t.school && t.grade)) return true;
  if (t.sch.id) return false;
  // 이름만 적어 둔 학교 → 전국 학교 목록이 있으면 정확한 학교를 한 번 고르게
  try { return (await fetch("schools.json", { method: "HEAD", cache: "no-cache" })).ok; } catch (e) { return false; }
}
async function showSchoolSetup() {
  const info = tbInfo();
  let grade = info.grade || "", picked = info.sch && info.sch.id ? { ...info.sch } : null;
  $("label").innerHTML = `우리 학교·학년<span class="sub">교과서 출판사</span>`;
  $("prev").style.visibility = $("next").style.visibility = "hidden"; $("goToday").hidden = true;
  $("view").innerHTML = `<div class="loading">학교 목록 불러오는 중…</div>`;
  const all = await loadSchools();
  const kindOf = g => g ? (g.startsWith("중") ? "중" : "고") : "";
  $("view").innerHTML = `<div class="panel"><h2>🏫 우리 학교와 학년을 알려 주세요</h2>
    <p class="empty">같은 학교 같은 학년 친구들이 등록한 교과서 출판사를 불러올게요.</p>
    <label class="lbl">지금 학년</label>
    <div class="tbgrades" id="suGrades">${GRADES.map(g => `<button data-g="${g}" class="${g === grade ? "on" : ""}">${g}</button>`).join("")}</div>
    <label class="lbl">학교</label>
    <div id="suPicked"></div>
    <input id="suSchool" value="${all ? "" : esc(info.school || "")}" placeholder="${all ? "학교 이름 검색 (예: 서울 ○○고, ○○중)" : "예) ○○고등학교"}" autocomplete="off" ${all ? "" : 'list="suSchools"'}>
    ${all ? `<div class="hint" style="font-size:12px;color:var(--muted);margin-top:4px">이름이 같은 학교가 많아요. 주소를 보고 우리 학교를 골라 주세요. 지역 이름을 같이 적으면 빨라요.</div>`
      : `<datalist id="suSchools"></datalist><div class="hint" style="font-size:12px;color:var(--muted);margin-top:4px">전국 학교 목록이 아직 준비되지 않아서 이름을 직접 적어요.</div>`}
    <div id="suResults" class="suresults"></div>
    <div id="suMsg" class="err" hidden></div>
    <div class="actions" style="margin-top:14px">
      <button class="btn ghost" id="suLater" style="margin-right:auto">나중에 할게요</button>
      <button class="btn" id="suNext">다음</button></div></div>`;
  const row = (o, k) => `<button class="suitem" data-k="${k}"><span class="nm">${esc(o.name)} <i>${o.kind === "중" ? "중학교" : "고등학교"}</i></span>
      ${o.jibun ? `<span class="ad">📍 지번 ${esc(o.jibun)}</span>` : ""}${o.road ? `<span class="ad">🛣️ 도로명 ${esc(o.road)}</span>` : ""}</button>`;
  const showPicked = () => {
    $("suPicked").innerHTML = picked ? `<div class="tbpicked"><span><b>✅ ${esc(picked.name)}</b>
      ${picked.addr ? `<small>📍 지번 ${esc(picked.addr)}</small>` : ""}${picked.road ? `<small>🛣️ 도로명 ${esc(picked.road)}</small>` : ""}
      ${picked.lat || picked.road || picked.addr ? `<small><a href="${esc(mapLink({ name: picked.name, lat: picked.lat, lng: picked.lng, road: picked.road, jibun: picked.addr }))}" target="_blank" rel="noopener noreferrer">🗺️ 지도에서 보기</a></small>` : ""}</span>
      <button class="btn ghost" id="suUnpick">바꾸기</button></div>` : "";
    $("suSchool").hidden = !!(all && picked);
    if (picked && $("suUnpick")) $("suUnpick").onclick = () => { picked = null; showPicked(); $("suSchool").focus(); };
  };
  let found = [];
  const doSearch = () => {
    if (!all || picked) { $("suResults").innerHTML = ""; return; }
    const q = $("suSchool").value; found = searchSchools(all, q, kindOf(grade));
    const sameName = n => found.filter(o => o.name === n).length;
    $("suResults").innerHTML = !q.trim() ? "" : !found.length ? `<div class="empty">찾는 학교가 없어요. 이름을 다르게 적어 보세요.${grade ? ` (${grade} 학년이라 ${kindOf(grade) === "중" ? "중학교" : "고등학교"}만 찾아요)` : ""}</div>`
      : found.slice(0, 30).map((o, k) => row(o, k).replace('</i></span>', `</i>${sameName(o.name) > 1 ? ` <em>같은 이름 ${sameName(o.name)}곳</em>` : ""}</span>`)).join("")
        + (found.length > 30 ? `<div class="empty">${found.length - 30}개 더 있어요. 지역 이름을 같이 적어 보세요 (예: 부산 ${esc(q.trim())})</div>` : "");
  };
  let timer = 0;
  $("suSchool").oninput = () => { clearTimeout(timer); timer = setTimeout(async () => {
    if (!$("suSchool")) return;
    if (all) return doSearch();
    const list = await sharedSchools($("suSchool").value);
    if ($("suSchools")) $("suSchools").innerHTML = list.map(r => `<option value="${esc(r.school)}">${r.people}명</option>`).join("");
  }, all ? 150 : 300); };
  $("suResults").onclick = ev => { const b = ev.target.closest(".suitem"); if (!b) return; const o = found[+b.dataset.k];
    picked = { name: o.name, id: o.id, addr: o.jibun || "", road: o.road || "", lat: o.lat, lng: o.lng, kind: o.kind }; showPicked(); doSearch(); };
  $("suGrades").onclick = ev => { const b = ev.target.closest("button[data-g]"); if (!b) return; grade = b.dataset.g;
    $("suGrades").querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b));
    if (picked && picked.kind && picked.kind !== kindOf(grade)) { picked = null; showPicked(); }
    doSearch(); };
  $("suLater").onclick = () => { store(tbSkipKey(), "1"); toast("☰ 메뉴 → 📚 교과서 출판사에서 언제든 정할 수 있어요"); load(); };
  $("suNext").onclick = async () => {
    const sch = all ? picked : ($("suSchool").value.trim() ? { name: $("suSchool").value.trim() } : null);
    if (!grade || !sch) { $("suMsg").hidden = false; $("suMsg").textContent = !grade ? "지금 학년을 골라 주세요" : all ? "목록에서 우리 학교를 눌러 골라 주세요" : "학교 이름을 적어 주세요"; return; }
    $("suNext").disabled = true; $("suNext").textContent = "찾는 중…";
    showSchoolChoices(sch, grade, await sharedChoices(sch, grade));
  };
  showPicked();
}
function showSchoolChoices(sch, grade, choices) {
  const school = sch.name;
  const me = tbInfo(), mine = sharedKey(me.sch) === sharedKey(sch) || !me.sch.id && schoolKey(me.school) === schoolKey(sch.name) ? cleanTb(me.textbooks[grade]) : [];
  const opts = [...(mine.length ? [{ list: mine, mine: true }] : []), ...(choices || []).filter(c => !(mine.length && sameTb(c.list, mine)))];
  const grid = list => `<div class="tbgrid">${list.map(t => `<div><span>${esc(t.subject)}</span><b>${esc(t.publisher || "-")}</b></div>`).join("")}</div>`;
  const head = choices === null && !mine.length
    ? `<p class="empty">친구들과 공유하는 기능이 아직 준비되지 않았어요. 우리 학교 출판사를 직접 적어 주세요.</p>`
    : opts.length
    ? `<p>같은 학교 같은 학년에서 등록한 교과서 출판사예요.<br><b>우리 학교 ${grade} 출판사가 이게 맞나요?</b></p>`
    : `<p>아직 <b>${esc(school)} ${grade}</b> 출판사를 등록한 사람이 없어요.<br>처음으로 등록해 주세요! 같은 학교 친구들이 쓸 수 있어요.</p>`;
  $("view").innerHTML = `<div class="panel"><h2>📚 ${esc(school)} · ${grade}</h2>${sch.addr || sch.road ? `<div class="empty" style="margin-top:-6px">📍 ${esc(sch.addr || sch.road)}</div>` : ""}${head}
    ${opts.map((o, k) => `<section class="day tbopt" style="margin:10px 0">
      <div class="dhead"><span class="date">${o.mine ? "지금 내 계정에 저장된 출판사" : opts.length > 1 ? `${k + 1}번` : "친구들이 등록한 출판사"}</span>
        ${o.people ? `<span class="chip">${o.people}명이 등록</span>` : ""}</div>${grid(o.list)}
      <button class="btn" data-k="${k}" style="width:100%;margin-top:10px">✅ ${opts.length > 1 ? "이게 맞아요" : "네, 맞아요"}</button></section>`).join("")}
    <div id="suMsg" class="err" hidden></div>
    <div class="actions" style="margin-top:12px;flex-wrap:wrap">
      <button class="btn ghost" id="suBack" style="margin-right:auto">‹ 뒤로</button>
      <button class="btn ${opts.length ? "ghost" : ""}" id="suOwn">✏️ ${opts.length ? "아니에요, 다르게 등록할게요" : "출판사 등록하기"}</button></div></div>`;
  $("suBack").onclick = () => showSchoolSetup();
  $("suOwn").onclick = () => {   // 직접 등록: 출판사 화면의 수정 칸으로 (첫 후보나 기본 과목을 미리 채움)
    const base = opts.length ? opts[0].list : tbBase(grade).map(x => ({ subject: x, publisher: "" }));
    tbDraft = { view: grade, sch, isCur: true, list: base.map(t => ({ ...t, publisher: opts.length ? t.publisher : "" })) };
    tbView = grade; store("tbgrade", grade); store(tbSkipKey(), "1");
    mode = "books"; store("mode", mode); load(); window.scrollTo({ top: 0 });
  };
  $("view").querySelectorAll(".tbopt button[data-k]").forEach(b => b.onclick = async () => {
    b.disabled = true; b.textContent = "저장 중…";
    try {
      await writeTb({ sch, view: grade, isCur: true, list: opts[+b.dataset.k].list });
      tbView = grade; store("tbgrade", grade); store(tbSkipKey(), "1");
      toast("✓ 우리 학교 출판사로 저장했어요"); mode = "books"; store("mode", mode); load();
    } catch (e) { b.disabled = false; b.textContent = "✅ 다시 시도"; $("suMsg").hidden = false; $("suMsg").textContent = "저장 실패: " + (e.message || e); }
  });
}

// 처음 로그인한 계정: 빈 시간표로 시작
async function showOnboard(msg) {
  $("view").innerHTML = `<div class="panel"><h2>👋 처음 오셨네요</h2>
    <p><b>${esc(sbUser.email || "")}</b> 계정으로 로그인했어요. 이 계정의 계획은 이 계정에서만 보여요.</p>
    <button class="btn" id="obFresh" style="width:100%;margin:6px 0">✨ 시작하기 (빈 시간표)</button>
    <p class="empty">시작한 뒤 ⚙️ 에서 기본 시간표와 ntfy 알림 토픽을 정할 수 있어요.</p>
    <div id="obMsg" class="empty">${esc(msg || "")}</div></div>`;
  $("obFresh").onclick = async () => {
    try { await updateFile("schedule.json", () => DEFAULT_SCHEDULE, "새로 시작"); start(); }
    catch (e) { $("obMsg").textContent = "저장 실패: " + (e.message || e); }
  };
}
function showSettings(err) {
  if (SB) return showAccount(err);
  $("view").innerHTML = `<div class="panel">
    <h2>처음 한 번만 설정</h2>
    <p>앱이 내 계획표를 고칠 수 있게 GitHub <b>토큰</b>을 한 번 넣어 주세요. 토큰은 이 휴대폰에만 저장돼요.</p>
    <ol>
      <li><a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">토큰 만들기 페이지</a> 열기</li>
      <li><b>Repository access</b>: <i>Only select repositories</i> → <b>alam</b> 선택</li>
      <li><b>Permissions</b> → <i>Repository permissions</i> → <b>Contents</b> → <b>Read and write</b></li>
      <li>맨 아래 <b>Generate token</b> → 나온 <code>github_pat_…</code>를 복사</li>
    </ol>
    <input id="tok" type="password" placeholder="github_pat_… 붙여넣기" autocomplete="off" value="${esc(token || "")}">
    ${err ? `<div class="err">${esc(err)}</div>` : ""}
    <div style="display:flex;gap:8px;margin-top:4px">
      <button class="btn" id="tokSave">저장하고 시작</button>
      ${token ? '<button class="btn ghost" id="tokCancel">취소</button><button class="btn ghost" id="tokDel">토큰 지우기</button>' : ""}
    </div></div>`;
  $("tokSave").onclick = () => { const v = $("tok").value.trim(); if (!v) return; token = v; store("token", v); start(); };
  if ($("tokCancel")) $("tokCancel").onclick = () => load();
  if ($("tokDel")) $("tokDel").onclick = () => { token = null; store("token", null); showSettings(); };
}
async function showAccount(err) {
  if (!sbUser) return showLogin(err);
  const st = await getFile("settings.json"); let cfg = {}; try { cfg = st ? JSON.parse(st.text) : {}; } catch (e) {}
  const sch = await getFile("schedule.json");
  $("view").innerHTML = `<div class="panel"><h2>⚙️ 계정 · 설정</h2>
    <p>로그인: <b>${esc(sbUser.email || "")}</b><br><span class="empty">이 계정의 계획·보고서·시험은 이 계정으로 로그인했을 때만 보여요.</span></p>
    <label class="lbl">🔔 ntfy 알림 토픽 <span class="empty">(ntfy 앱에서 구독한 이름. 비우면 알림 안 와요)</span></label>
    <div style="display:flex;gap:6px"><input id="ntfy" value="${esc(cfg.ntfy_topic || "")}" placeholder="예) alam-8f3k2q9xw7mz" autocomplete="off" spellcheck="false" style="flex:1">
      <button class="btn ghost" id="ntfyGen" type="button" title="추측하기 어려운 이름 만들기">🎲</button></div>
    <div id="ntfyWarn" class="empty" style="font-size:12px;margin-top:4px"></div>
    <label class="lbl">📋 기본 시간표 (고급: JSON)</label>
    <textarea id="schJson" class="sbox" style="min-height:160px;font-family:ui-monospace,monospace;font-size:12px">${esc(sch ? sch.text : "")}</textarea>
    ${err ? `<div class="err">${esc(err)}</div>` : ""}<div id="setMsg" class="empty"></div>
    <div class="actions" style="margin-top:10px;flex-wrap:wrap">
      <button class="btn ghost danger" id="logout" style="margin-right:auto">로그아웃</button>
      <button class="btn ghost" id="setCancel">닫기</button><button class="btn" id="setSave">저장</button></div>
</div>`;
  $("logout").onclick = async () => {
    try { await SB.auth.signOut(); } catch (e) {}
    // 🔒 이 기기에 남은 내 데이터도 지우고 새로 시작 (같은 기기를 다른 사람이 써도 안 보이게)
    for (const k of ["token", "learn", "places"]) store(k, null);
    files.clear(); sbUser = null; sbAll = false;
    location.replace(location.pathname);
  };
  // 🔒 ntfy.sh 토픽은 이름만 알면 누구나 구독해서 내 알림(일정)을 볼 수 있어요 → 길고 무작위인 이름 권장
  const topicOk = t => /^[A-Za-z0-9_-]{1,64}$/.test(t);
  const topicWarn = () => {
    const t = $("ntfy").value.trim();
    $("ntfyWarn").innerHTML = !t ? "" : !topicOk(t) ? `<span class="err">영문·숫자·_- 만, 64자까지 쓸 수 있어요</span>`
      : t.length < 12 || !/\d/.test(t) ? "⚠️ 이름이 짧거나 쉬우면 다른 사람이 같은 토픽을 구독해 내 알림을 볼 수 있어요. 🎲 로 바꾸고 ntfy 앱에서도 새 이름으로 구독하세요."
      : "🔒 토픽 이름은 비밀번호처럼 남에게 알려 주지 마세요.";
  };
  $("ntfy").oninput = topicWarn; topicWarn();
  $("ntfyGen").onclick = () => {
    const a = "abcdefghijkmnpqrstuvwxyz23456789", r = crypto.getRandomValues(new Uint8Array(16));
    $("ntfy").value = "alam-" + Array.from(r, b => a[b % a.length]).join(""); topicWarn();
  };
  $("setCancel").onclick = () => load();
  $("setSave").onclick = async () => {
    try {
      const sj = $("schJson").value; JSON.parse(sj);
      cfg.ntfy_topic = $("ntfy").value.trim();
      if (cfg.ntfy_topic && !topicOk(cfg.ntfy_topic)) { $("setMsg").textContent = "ntfy 토픽은 영문·숫자·_- 만 쓸 수 있어요"; return; }
      await updateFile("settings.json", () => JSON.stringify(cfg, null, 2) + "\n", "설정");
      await updateFile("schedule.json", () => sj, "기본 시간표");
      schedule = JSON.parse(sj); toast("저장됨 ✓"); load();
    } catch (e) { $("setMsg").textContent = e instanceof SyntaxError ? "시간표 JSON 형식이 틀렸어요: " + e.message : (e.message || e); }
  };
}
$("openSettings").onclick = () => showSettings();

async function start() {
  if (SB) {
    $("view").innerHTML = `<div class="loading">불러오는 중…</div>`;
    try {
      const { data } = await SB.auth.getSession();
      if (!data.session) return showLogin();
      sbUser = data.session.user;
      await sbLoadAll();
      const s = await getFile("schedule.json");
      if (!s) return showOnboard();
      schedule = JSON.parse(s.text);
      if (await needSchoolSetup()) return showSchoolSetup();
      return load();
    } catch (e) { return showLogin(e.message || String(e)); }
  }
  if (CFG.supabaseUrl && !window.supabase) { $("view").innerHTML = `<div class="panel"><div class="err">로그인 모듈을 불러오지 못했어요. 인터넷 연결을 확인하고 ↻ 를 눌러 주세요.</div></div>`; return; }
  if (!token) return showSettings();
  $("view").innerHTML = `<div class="loading">불러오는 중…</div>`;
  try {
    const repo = await api("");
    if (!repo) throw Object.assign(new Error("저장소를 찾을 수 없어요. 토큰에서 alam 저장소를 선택했는지 확인하세요."), { status: 0 });
    branch = repo.default_branch;
    const s = await getFile("schedule.json");
    schedule = JSON.parse(s.text);
    await load();
  } catch (e) {
    showSettings(e.status === 401 ? "토큰이 틀렸거나 만료됐어요." : (e.message || String(e)));
  }
}
start();
