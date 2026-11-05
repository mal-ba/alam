#!/usr/bin/env python3
"""자정마다 실행되는 일정 알람 + 일/주/월 계획표 관리 스크립트.

일정이 정해지는 우선순위 (위에 있을수록 먼저 적용):
  1. 주간 계획표  plans/week/YYYY-MM-DD.md   (그 주 일요일 날짜가 파일 이름)
  2. 월간 계획표  plans/month/YYYY-MM.md
  3. 기본 시간표  schedule.json (요일마다 반복)

자정에 하는 일:
  - 매월 1일   : 그달 월간 계획표를 만들고(없을 때만) 알림  (2일에 한 번 더 알림)
  - 매주 일요일: 그 주(일~토) 주간 계획표를 만들고(없을 때만) 알림
  - 매일       : plans/today.md 를 새로 쓰고, 오늘 일정 요약 + 시간별 알람 예약

사용법:
  python alarm.py                         # 실제 실행 (NTFY_TOPIC 환경변수 필요)
  python alarm.py --dry-run               # 보내지도, 파일을 쓰지도 않고 미리보기만
  python alarm.py --date 2026-11-08 --dry-run
  python alarm.py --make-month 2026-12    # 월간 표 미리 만들기
  python alarm.py --make-week 2026-11-15  # 그 날짜가 들어있는 주의 주간 표 미리 만들기
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]
BASE_DIR = Path(__file__).resolve().parent
PLANS = BASE_DIR / "plans"
NTFY_LIMIT = 3500  # ntfy 메시지 최대 4096바이트. 넉넉히 자름

EVENT_RE = re.compile(
    r"^(\d{1,2}):(\d{2})(?:\s*[~\-]\s*(\d{1,2}):(\d{2}))?\s+(.+?)\s*(?:\[([\d,\s]*)\])?$"
)

HOW_TO_EDIT = """\
> **고치는 법** (오른쪽 위 연필 ✏️ 버튼 → 수정 → Commit changes)
> - `일정` 칸: `시간 제목`을 쉼표(`,`)로 구분해서 적어요. 시간이 있는 일정은 알람이 와요.
>   - 예) `08:45 등교, 18:00~21:00 야자, 19:00 친구 생일 [60,10]`
>   - 끝에 `[60,10]`처럼 쓰면 60분 전·10분 전에 알림 (안 쓰면 기본값)
>   - `[0]`은 정각에 알림, `[]`는 알림 없음
> - `할 일·메모` 칸: 시간 없이 적고 싶은 것 (아침 요약 알림에 같이 와요)
> - 그날 일정을 다 지우면 그날은 일정 없음으로 처리돼요.
"""


# ---------------------------------------------------------------- 데이터

def load_schedule(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Planner:
    def __init__(self, schedule):
        self.schedule = schedule
        self.default_remind = schedule.get("default_remind_before", [10])
        # 같은 제목의 기본 일정과 같은 알림 타이밍을 쓰도록
        self.remind_by_title = {}
        for events in schedule["weekly"].values():
            for ev in events:
                self.remind_by_title.setdefault(ev["title"], ev.get("remind_before", [0]))
        self._cache = {}

    # --- 파일 경로
    @staticmethod
    def week_start(d):
        return d - timedelta(days=(d.weekday() + 1) % 7)  # 일요일 시작

    @staticmethod
    def week_path(d):
        return PLANS / "week" / f"{Planner.week_start(d).isoformat()}.md"

    @staticmethod
    def month_path(d):
        return PLANS / "month" / f"{d.year:04d}-{d.month:02d}.md"

    # --- 하루 일정 구하기
    # --- 학교 (시간표, 휴업일, 방학)
    @property
    def school(self):
        return self.schedule.get("school", {})

    def school_off(self, d):
        """학교 안 가는 날이면 이유, 아니면 None."""
        off = self.school.get("off_days", {}).get(d.isoformat())
        if off:
            return off
        for v in self.school.get("vacations", []):
            if v["from"] <= d.isoformat() <= v["to"]:
                return v["name"]
        return None

    def is_school_day(self, d):
        titles = set(self.school.get("school_events", []))
        weekly = self.schedule["weekly"].get(str(d.weekday()), [])
        return not self.school_off(d) and any(ev["title"] in titles for ev in weekly)

    def exam(self, d):
        return self.school.get("exam_days", {}).get(d.isoformat())

    def classes(self, d):
        """그날 교시별 과목 목록. 학교 안 가거나 시험날이거나 시간표가 없으면 []."""
        until = self.school.get("timetable_until")
        if self.school_off(d) or self.exam(d) or (until and d.isoformat() > until):
            return []
        subjects = list(self.school.get("timetable", {}).get(str(d.weekday()), []))
        alt = self.school.get("alternating")
        if alt and d.weekday() == alt["weekday"] and subjects:
            ref = date.fromisoformat(alt["ref_date"])
            n = (self.week_start(d) - self.week_start(ref)).days // 7
            pick = alt["options"][n % len(alt["options"])]
            for period in alt["periods"]:
                if period <= len(subjects):
                    subjects[period - 1] = pick
        return subjects

    def base_day(self, d):
        events = [dict(ev) for ev in self.schedule["weekly"].get(str(d.weekday()), [])]
        for ev in events:
            ev.setdefault("remind_before", [0])
        memos = []
        off = self.school_off(d)
        if off:
            school_titles = set(self.school.get("school_events", []))
            events = [ev for ev in events if ev["title"] not in school_titles]
            memos.append(f"🏫 {off} - 학교 안 감")
        exam = None if off else self.exam(d)
        if exam:
            keep = set(self.school.get("exam_keep_events", ["등교"]))
            school_titles = set(self.school.get("school_events", [])) - keep
            events = [ev for ev in events if ev["title"] not in school_titles]
            memos.append(f"✏️ {exam} - 등교만 (하교·야자 없음)")
        note = self.school.get("notes", {}).get(d.isoformat())
        if note:
            memos.append(note)
        return {"events": events, "memos": [m.replace(",", "·").replace("|", " ") for m in memos]}

    def day(self, d):
        for path, ref in ((self.week_path(d), self.week_start(d)), (self.month_path(d), d.replace(day=1))):
            table = self.read_table(path, ref)
            if d in table:
                return table[d]
        return self.base_day(d)

    def source_of(self, d):
        for path, ref in ((self.week_path(d), self.week_start(d)), (self.month_path(d), d.replace(day=1))):
            if d in self.read_table(path, ref):
                return path.relative_to(BASE_DIR).as_posix()
        return "schedule.json"

    # --- 표 읽기
    def read_table(self, path, ref):
        if path in self._cache:
            return self._cache[path]
        result = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if not line.strip().startswith("|") or len(cells) < 2:
                    continue
                m = re.match(r"^(\d{1,2})\s*/\s*(\d{1,2})", cells[0])
                if not m:
                    continue  # 머리줄, 구분줄
                month, dd = int(m.group(1)), int(m.group(2))
                year = ref.year + (1 if month < ref.month else 0)  # 12월→1월 넘어가는 주
                try:
                    d = date(year, month, dd)
                except ValueError:
                    print(f"경고: {path.name} 의 날짜 '{cells[0]}' 를 이해하지 못했어요", file=sys.stderr)
                    continue
                result[d] = self.parse_cells(cells[1], cells[2] if len(cells) > 2 else "")
        self._cache[path] = result
        return result

    def parse_cells(self, events_cell, memo_cell):
        events, memos = [], []
        for item in split_items(events_cell):
            m = EVENT_RE.match(item)
            if not m:
                memos.append(item)  # 시간이 없으면 메모로
                continue
            h1, m1, h2, m2, title, remind = m.groups()
            ev = {"title": title, "start": f"{int(h1):02d}:{m1}"}
            if h2:
                ev["end"] = f"{int(h2):02d}:{m2}"
            if remind is not None:
                ev["remind_before"] = [int(x) for x in remind.replace(" ", "").split(",") if x]
            else:
                ev["remind_before"] = self.remind_by_title.get(title, self.default_remind)
            events.append(ev)
        memos += split_items(memo_cell)
        events.sort(key=lambda e: e["start"])
        return {"events": events, "memos": memos}

    # --- 표 쓰기
    def format_event(self, ev):
        span = f"{ev['start']}~{ev['end']}" if ev.get("end") else ev["start"]
        text = f"{span} {ev['title']}"
        if ev.get("remind_before") != self.remind_by_title.get(ev["title"], self.default_remind):
            text += " [" + ",".join(str(x) for x in ev.get("remind_before", [])) + "]"
        return text

    def row(self, d):
        day = self.day(d)
        events = ", ".join(self.format_event(e) for e in day["events"])
        memos = ", ".join(day["memos"])
        return f"| {d:%m/%d} ({WEEKDAY_KO[d.weekday()]}) | {events} | {memos} |"

    def table_md(self, title, days):
        lines = [f"# {title}", "", HOW_TO_EDIT, "| 날짜 | 일정 | 할 일·메모 |", "|---|---|---|"]
        lines += [self.row(d) for d in days]
        return "\n".join(lines) + "\n"

    def make_month(self, d, overwrite=False):
        first = d.replace(day=1)
        path = self.month_path(first)
        if path.exists() and not overwrite:
            return path, False
        days = []
        cur = first
        while cur.month == first.month:
            days.append(cur)
            cur += timedelta(days=1)
        return self._write(path, self.table_md(f"{first.year}년 {first.month}월 계획표", days)), True

    def make_week(self, d, overwrite=False):
        start = self.week_start(d)
        path = self.week_path(start)
        if path.exists() and not overwrite:
            return path, False
        days = [start + timedelta(days=i) for i in range(7)]
        end = days[-1]
        title = f"주간 계획표 ({start:%Y.%m.%d} 일 ~ {end:%m.%d} 토)"
        return self._write(path, self.table_md(title, days)), True

    def make_today(self, d):
        day = self.day(d)
        lines = [
            f"# 오늘 계획 — {d:%Y.%m.%d} ({WEEKDAY_KO[d.weekday()]})",
            "",
            f"> 이 파일은 매일 자정에 자동으로 새로 써져요. 고치려면 `{self.source_of(d)}` 를 수정하세요.",
            "",
            "| 시간 | 일정 | 알림 |",
            "|---|---|---|",
        ]
        for ev in day["events"]:
            span = f"{ev['start']}~{ev['end']}" if ev.get("end") else ev["start"]
            rb = ev.get("remind_before", [])
            remind = ", ".join("정각" if x == 0 else f"{x}분 전" for x in rb) or "없음"
            lines.append(f"| {span} | {ev['title']} | {remind} |")
        if not day["events"]:
            lines.append("| - | 일정 없음 | - |")
        if day["memos"]:
            lines += ["", "## 할 일·메모", ""] + [f"- [ ] {m}" for m in day["memos"]]
        classes = self.classes(d)
        if classes:
            times = self.school.get("period_times", [])
            lines += ["", "## 📚 시간표", "", "| 교시 | 과목 |", "|---|---|"]
            lines += [f"| {i}교시{f' ({times[i-1]})' if i <= len(times) else ''} | {c} |" for i, c in enumerate(classes, 1)]
        return self._write(PLANS / "today.md", "\n".join(lines) + "\n")

    def _write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self._cache.clear()
        return path


def read_section(path, name):
    """표 파일의 '## name' 아래 줄들 (앱의 목표·MEMO·GRIT 칸)."""
    if not path.exists():
        return []
    out, inside = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == f"## {name}":
            inside = True
            continue
        if inside and re.match(r"^## |^> \*\*고치는|^\| 날짜", line):
            break
        if inside and line.strip():
            out.append(line.strip())
    return out


def bullets(path, name):
    return [re.sub(r"^[-*]\s*", "", l) for l in read_section(path, name)]


def grit_lines(path):
    rows = []
    for l in read_section(path, "💪 GRIT"):
        if l.startswith("|") and not re.match(r"^\|\s*(과목|-)", l):
            c = [x.strip() for x in l.strip("|").split("|")]
            c = (c + ["", "", ""])[:3]
            if c[1]:  # 내용 없는 과목은 생략
                rows.append(" ".join(x for x in c if x))
    return rows


def split_items(cell):
    """쉼표로 나누되 [60,10] 같은 대괄호 안의 쉼표는 무시."""
    return [x.strip() for x in re.split(r",(?![^\[]*\])", cell) if x.strip()]


# ---------------------------------------------------------------- 알림 문구

def span_of(ev):
    return f"{ev['start']}~{ev['end']}" if ev.get("end") else ev["start"]


def day_line(planner, d, with_date=True):
    day = planner.day(d)
    parts = [f"{span_of(e)} {e['title']}" for e in day["events"]] + [f"📝{m}" for m in day["memos"]]
    text = ", ".join(parts) if parts else "쉬는 날"
    return f"{d:%m/%d}({WEEKDAY_KO[d.weekday()]}) {text}" if with_date else text


def report_lists(d):
    """plans/report/YYYY-MM-DD.md 에서 '외워야 할 것', '기억해야 할 것' 목록을 읽는다."""
    path = PLANS / "report" / f"{d.isoformat()}.md"
    out = {"memorize": [], "remember": []}
    if not path.exists():
        return out
    sec = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            sec = "memorize" if "외워" in line else "remember" if "기억" in line else None
        elif sec and re.match(r"^\s*[-*]\s+\S", line):
            out[sec].append(re.sub(r"^\s*[-*]\s+", "", line).strip())
    return out


def report_extras(d):
    """d 날짜 보고서의 외울 것·기억할 것 줄들."""
    prev = report_lists(d)
    lines = []
    if prev["memorize"]:
        lines += ["🧠 어제 외워야 할 것"] + [f"· {x}" for x in prev["memorize"]]
    if prev["remember"]:
        lines += ([""] if lines else []) + ["📌 기억해야 할 것"] + [f"· {x}" for x in prev["remember"]]
    return lines


def exam_lines(d, within=14):
    """plans/exams.json 에서 d 기준 within일 안의 시험 (D-day, 진도)."""
    path = PLANS / "exams.json"
    if not path.exists():
        return []
    try:
        exams = json.loads(path.read_text(encoding="utf-8")).get("exams", [])
    except ValueError:
        return []
    def days_to(s):
        try:
            return (date.fromisoformat(s) - d).days
        except (TypeError, ValueError):
            return None

    def prog(ranges):
        return round(sum(int(r.get("progress", 0) or 0) for r in ranges) / len(ranges)) if ranges else 0

    def dday(n):
        return "D-DAY" if n == 0 else f"D-{n}"

    out = []
    for x in sorted(exams, key=lambda x: x.get("date") or "9999"):
        n = days_to(x.get("date"))
        subjects = x.get("subjects")
        if x.get("kind") != "수행" and isinstance(subjects, list):
            # 정기시험: 과목별 시험날이 있으면 과목마다, 없으면 시험 하나로
            name = x.get("name") or "정기시험"
            dated = [(days_to(v.get("date")), v) for v in subjects if v.get("date")]
            hits = [(m, v) for m, v in dated if m is not None and 0 <= m <= within]
            for m, v in hits:
                out.append(f"{dday(m)} [시험] {name} {v.get('subject', '')} (진도 {prog(v.get('ranges') or [])}%)")
            if not hits and n is not None and 0 <= n <= within:
                rs = [r for v in subjects for r in (v.get("ranges") or [])]
                subs = "·".join(v.get("subject", "") for v in subjects if v.get("subject"))
                out.append(f"{dday(n)} [시험] {name}{f' ({subs})' if subs else ''} (진도 {prog(rs)}%)")
            continue
        if n is not None and 0 <= n <= within:
            kind = "수행" if x.get("kind") == "수행" else "시험"
            name = " ".join(v for v in (x.get("subject", ""), x.get("name", "")) if v)
            out.append(f"{dday(n)} [{kind}] {name} (진도 {prog(x.get('ranges') or [])}%)")
    return out


def daily_summary(planner, d, with_report=True):
    day = planner.day(d)
    head = f"{d:%m/%d} ({WEEKDAY_KO[d.weekday()]}) 오늘 일정"
    lines = [f"- {span_of(e)} {e['title']}" for e in day["events"]]
    lines += [f"📝 {m}" for m in day["memos"]]
    if not lines:
        lines = ["오늘은 일정이 없어요. 푹 쉬세요!"]
    classes = planner.classes(d)
    if classes:
        lines += ["", "📚 시간표: " + " · ".join(f"{"①②③④⑤⑥⑦⑧⑨"[i-1] if i <= 9 else i}{c}" for i, c in enumerate(classes, 1))]
    exams = exam_lines(d)
    if exams:
        lines += ["", "📝 다가오는 시험"] + [f"· {x}" for x in exams]
    # 어제 쓴 수업 보고서에서 외울 것 / 기억할 것
    extra = report_extras(d - timedelta(days=1)) if with_report else []
    if extra:
        lines += [""] + extra
    return head, clip("\n".join(lines))


def build_alarms(planner, d, tz):
    alarms = []
    for ev in planner.day(d)["events"]:
        h, m = map(int, ev["start"].split(":"))
        start = datetime(d.year, d.month, d.day, h, m, tzinfo=tz)
        for before in ev.get("remind_before", []):
            when = start - timedelta(minutes=before)
            body = f"{before}분 뒤 {ev['title']} ({span_of(ev)})" if before > 0 else f"지금 {ev['title']} ({span_of(ev)})"
            alarms.append((when, ev["title"], body))
    alarms.sort(key=lambda a: a[0])
    return alarms


def clip(text):
    if len(text.encode("utf-8")) <= NTFY_LIMIT:
        return text
    out = []
    for line in text.splitlines():
        if len("\n".join(out + [line]).encode("utf-8")) > NTFY_LIMIT - 60:
            out.append("… (알림을 누르면 전체 표가 열려요)")
            break
        out.append(line)
    return "\n".join(out)


def app_url(query=""):
    if os.environ.get("ALAM_APP_URL"):
        return os.environ["ALAM_APP_URL"].rstrip("/") + "/" + query
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        return None
    owner, name = repo.split("/", 1)
    return f"https://{owner.lower()}.github.io/{name}/{query}"


def todo_reminders(planner, d, tz):
    """'오늘 해야 할 일' 알림 목록 [(시각, 제목, 내용)]. 자정 기준 할 일 목록으로 만들어요.
    - commute_at(08:00) 알림엔 등교 시간을 맨 위에 같이 (등교 알람은 따로 안 울림)
    - remaining_from(21:00) 이후 알림에만 남은 일정(진행 중 포함)을 붙임"""
    cfg = planner.schedule.get("todo_reminders")
    if not cfg:
        return []
    times = list(cfg.get("daily", [])) + list(cfg.get("weekday", {}).get(str(d.weekday()), []))
    commute_at, remaining_from = cfg.get("commute_at"), cfg.get("remaining_from", "00:00")
    day = planner.day(d)
    todos = [m for m in day["memos"] if not m.startswith(("✅", "🏫", "✏️"))]
    commute = [e for e in day["events"] if e["title"] == "등교"]
    out = []
    for t in sorted(set(times)):
        h, m = map(int, t.split(":"))
        when = datetime(d.year, d.month, d.day, h, m, tzinfo=tz)
        lines = []
        if t == commute_at and commute:
            sh, sm = map(int, commute[0]["start"].split(":"))
            left = (sh * 60 + sm) - (h * 60 + m)
            lines += [f"🏫 {commute[0]['start']} 등교" + (f" ({left}분 남음)" if left > 0 else ""), ""]
        lines += ["☑️ 할 일"] + ([f"· {x}" for x in todos] or ["· 아직 없어요. 앱에서 오늘 할 일을 적어 보세요!"])
        if t >= remaining_from:
            def ends_after(e):  # 끝 시간이 시작보다 이르면(예: 10:30~00:00) 자정 넘어 끝나는 것
                end = e.get("end")
                return bool(end) and (end <= e["start"] or end > t)
            later = [e for e in day["events"] if e["start"] >= t or ends_after(e)]
            lines += ["", "⏰ 남은 일정"] + ([f"· {span_of(e)} {e['title']}" for e in later] or ["· 오늘 남은 일정 없음"])
        title = f"📋 오늘 해야 할 일 ({len(todos)}개)" + (" · 등교" if t == commute_at and commute else "")
        out.append((when, title, clip("\n".join(lines))))
    return out


def report_reminder(planner, d, tz):
    """밤에 '오늘 보고서 쓰기' 알림 (시각, 제목, 내용) 또는 None."""
    cfg = planner.schedule.get("report_reminder")
    if not cfg:
        return None
    if cfg.get("only_school_days", True) and not planner.is_school_day(d):
        return None
    h, m = map(int, cfg.get("time", "23:30").split(":"))
    when = datetime(d.year, d.month, d.day, h, m, tzinfo=tz)
    subjects = [c for c in dict.fromkeys(planner.classes(d)) if c not in ("창체", "동아리", "진로")]
    school_titles = set(planner.school.get("school_events", []))
    others = [e["title"] for e in planner.day(d)["events"] if e["title"] not in school_titles]
    lines = []
    if subjects:
        lines.append("오늘 수업: " + ", ".join(subjects))
    if others:
        lines.append("오늘 일정: " + ", ".join(dict.fromkeys(others)))
    lines.append("오늘 배운 것, 중요한 것, 외울 것을 정리해요." if subjects or others
                 else "오늘 공부한 것, 기억할 것을 정리해요.")
    body = "\n".join(lines)
    return when, "📒 오늘 보고서 쓸 시간", body


def github_url(path):
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        return None
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    ref = os.environ.get("GITHUB_REF_NAME", "main")
    return f"{server}/{repo}/blob/{ref}/{Path(path).relative_to(BASE_DIR).as_posix()}"


# ---------------------------------------------------------------- 전송

class Notifier:
    def __init__(self, server, topic, dry_run):
        self.server, self.topic, self.dry_run = server.rstrip("/"), topic, dry_run

    def send(self, title, message, at=None, tags="alarm_clock", click=None, priority="high"):
        if self.dry_run:
            return
        req = urllib.request.Request(f"{self.server}/{self.topic}", data=message.encode("utf-8"), method="POST")
        # HTTP 헤더는 ASCII만 되므로 RFC 2047 인코딩 (ntfy 지원)
        req.add_header("Title", "=?UTF-8?B?" + base64.b64encode(title.encode()).decode() + "?=")
        req.add_header("Tags", tags)
        req.add_header("Priority", priority)
        if click:
            req.add_header("Click", click)
        if at is not None:
            req.add_header("At", str(int(at.timestamp())))
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()


# ---------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description="자정 일정 알람 + 계획표")
    p.add_argument("--dry-run", action="store_true", help="보내지도, 파일을 쓰지도 않고 미리보기만")
    p.add_argument("--date", help="YYYY-MM-DD (기본: 낮 12시 이후면 내일, 그 전이면 오늘 · 한국시간)")
    p.add_argument("--schedule", default=str(BASE_DIR / "schedule.json"))
    p.add_argument("--make-month", metavar="YYYY-MM", help="월간 계획표만 만들고 끝")
    p.add_argument("--make-week", metavar="YYYY-MM-DD", help="그 날짜가 속한 주의 주간 계획표만 만들고 끝")
    p.add_argument("--overwrite", action="store_true", help="--make-* 때 기존 표를 덮어쓰기")
    p.add_argument("--force", action="store_true", help="오늘 이미 예약했어도 다시 예약 (알람이 두 번 올 수 있음)")
    args = p.parse_args()

    schedule = load_schedule(args.schedule)
    planner = Planner(schedule)

    if args.make_month or args.make_week:
        if args.make_month:
            path, made = planner.make_month(datetime.strptime(args.make_month, "%Y-%m").date(), args.overwrite)
            print(("만듦: " if made else "이미 있음: ") + str(path.relative_to(BASE_DIR)))
        if args.make_week:
            path, made = planner.make_week(datetime.strptime(args.make_week, "%Y-%m-%d").date(), args.overwrite)
            print(("만듦: " if made else "이미 있음: ") + str(path.relative_to(BASE_DIR)))
        return

    tz = timezone(timedelta(hours=schedule.get("timezone_offset_hours", 9)))
    now = datetime.now(tz)
    if os.environ.get("ALAM_NOW"):   # 테스트용: 지금 시각 바꾸기 (예: 2026-11-04T22:00)
        now = datetime.fromisoformat(os.environ["ALAM_NOW"]).replace(tzinfo=tz)
    # 밤(12시 이후) 실행 = 내일 알람을 미리 예약 / 새벽~오전 실행 = 오늘 (밤 실행이 실패했을 때 대신)
    evening = not args.date and now.hour >= 12
    today = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date \
        else now.date() + timedelta(days=1 if evening else 0)
    midnight = datetime(today.year, today.month, today.day, tzinfo=tz)
    at0 = midnight if midnight > now + timedelta(seconds=30) else None   # 요약은 그날 0시에 오게

    topic = os.environ.get("NTFY_TOPIC", "").strip()
    server = os.environ.get("NTFY_SERVER", "").strip() or "https://ntfy.sh"
    # 하루에 한 번만 예약 (수동 실행·늦게 돈 자동 실행이 겹쳐 알람이 두 번 오는 것 방지)
    marker, extras_marker = PLANS / ".scheduled", PLANS / ".extras"
    read = lambda f: f.read_text(encoding="utf-8").strip() if f.exists() else ""
    if not topic and not args.dry_run:
        sys.exit("NTFY_TOPIC 환경변수가 없습니다. (README 참고)")
    notify = Notifier(server, topic, args.dry_run)
    if not args.dry_run and not args.force and not args.date and read(marker) == today.isoformat():
        print(f"{today} 알람은 이미 예약했어요.")
        # 자정 실행: 어젯밤 늦게 쓴 보고서의 외울 것·기억할 것만 따로 보냄 (하루 한 번)
        if not evening and read(extras_marker) != today.isoformat():
            extra = report_extras(today - timedelta(days=1))
            if extra:
                print("[보고서] " + " / ".join(extra))
                notify.send("🧠 어제 보고서 복습", clip("\n".join(extra)), tags="brain", priority="default",
                            click=app_url(f"?report={(today - timedelta(days=1)).isoformat()}"))
            extras_marker.write_text(today.isoformat() + "\n", encoding="utf-8")
        return

    # 1) 월간 계획표: 1일에 만들고, 1일·2일에 알림
    if today.day in (1, 2):
        path = planner.month_path(today)
        if not args.dry_run:
            path, made = planner.make_month(today)
            print(("월간 표 만듦: " if made else "월간 표 있음: ") + path.relative_to(BASE_DIR).as_posix())
        first = today.replace(day=1)
        days, cur = [], first
        while cur.month == first.month:
            days.append(cur)
            cur += timedelta(days=1)
        title = f"📅 {today.month}월 계획표" + (" (다시 알림)" if today.day == 2 else "")
        goals = bullets(path, "🎯 이달의 목표")
        head = (["🎯 목표"] + [f"· {g}" for g in goals] + [""]) if goals else []
        body = clip("\n".join(head + [day_line(planner, d) for d in days]))
        print(f"[월간] {title}\n{body}\n")
        notify.send(title, body, at=at0, tags="calendar", click=app_url("?mode=month"), priority="default")

    # 2) 주간 계획표: 일요일에 만들고 알림
    if today.weekday() == 6:
        path = planner.week_path(today)
        if not args.dry_run:
            path, made = planner.make_week(today)
            print(("주간 표 만듦: " if made else "주간 표 있음: ") + path.relative_to(BASE_DIR).as_posix())
        days = [today + timedelta(days=i) for i in range(7)]
        title = f"🗓️ 이번 주 계획표 ({days[0]:%m/%d}~{days[-1]:%m/%d})"
        grit, must = grit_lines(path), bullets(path, "✅ MUST DO")
        head = (["💪 GRIT"] + [f"· {g}" for g in grit] + [""] if grit else []) + (["✅ MUST DO"] + [f"· {m}" for m in must] + [""] if must else [])
        body = clip("\n".join(head + [day_line(planner, d) for d in days]))
        print(f"[주간] {title}\n{body}\n")
        notify.send(title, body, at=at0, tags="spiral_calendar", click=app_url("?mode=week"), priority="default")

    # 3) 일간 계획표 + 알람
    if not args.dry_run:
        planner.make_today(today)
    # 밤에 미리 예약할 땐 보고서가 아직 안 끝났을 수 있으니, 외울 것은 자정 실행이 따로 보냄
    head, body = daily_summary(planner, today, with_report=not evening)
    print(f"[일간] {head}  (출처: {planner.source_of(today)}){f'  {at0:%m/%d %H:%M} 도착' if at0 else ''}\n{body}\n")
    notify.send(head, body, at=at0, tags="sunrise", click=app_url(f"?day={today.isoformat()}"), priority="default")

    for when, title, msg in build_alarms(planner, today, tz):
        # 실행이 늦어져 이미 지난 알람은 건너뜀 (ntfy는 과거 시각 예약 불가)
        if not args.date and when <= now + timedelta(seconds=30):
            print(f"  건너뜀(이미 지남) {when:%H:%M} {msg}")
            continue
        print(f"  예약 {when:%H:%M}  {msg}")
        notify.send(title, msg, at=when)

    for when, title, msg in todo_reminders(planner, today, tz):
        if not args.date and when <= now + timedelta(seconds=30):
            print(f"  건너뜀(이미 지남) {when:%H:%M} 할 일 알림")
            continue
        print(f"  예약 {when:%H:%M}  {title}")
        notify.send(title, msg, at=when, tags="clipboard", priority="default",
                    click=app_url(f"?day={today.isoformat()}"))

    rr = report_reminder(planner, today, tz)
    if rr:
        when, title, msg = rr
        if not args.date and when <= now + timedelta(seconds=30):
            print(f"  건너뜀(이미 지남) {when:%H:%M} 보고서 알림")
        else:
            print(f"  예약 {when:%H:%M}  {title}")
            notify.send(title, msg, at=when, tags="notebook", priority="default",
                        click=app_url(f"?report={today.isoformat()}"))

    if not args.dry_run and not args.date:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(today.isoformat() + "\n", encoding="utf-8")
        if not evening:   # 아침에 대신 예약했으면 요약에 외울 것이 이미 들어갔음
            extras_marker.write_text(today.isoformat() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
