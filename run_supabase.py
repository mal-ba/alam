#!/usr/bin/env python3
"""Supabase 에 저장된 계정별 계획으로 알람을 예약해요 (GitHub Actions 에서 실행).

- 환경변수: SUPABASE_URL, SUPABASE_SERVICE_KEY (GitHub Secrets 에만 넣기!)
- settings.json 에 ntfy_topic 이 있는 계정마다 alarm.py 와 같은 로직을 돌려요.
- 공개 저장소의 Actions 로그에는 개인 정보(이메일·일정 내용)를 찍지 않아요. 개수만 찍어요.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import traceback
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

import alarm

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]


def rest(method, path, body=None, prefer=None):
    req = urllib.request.Request(f"{URL}/rest/v1/{path}", method=method,
                                 data=None if body is None else json.dumps(body).encode("utf-8"))
    req.add_header("apikey", KEY)
    if not KEY.startswith("sb_secret_"):   # 예전 service_role(JWT) 키만 Authorization 에도 넣음
        req.add_header("Authorization", f"Bearer {KEY}")
    req.add_header("Content-Type", "application/json")
    if prefer:
        req.add_header("Prefer", prefer)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


def safe_path(p):
    pp = PurePosixPath(p)
    return not pp.is_absolute() and ".." not in pp.parts and p.strip() == p and p


def run_user(uid, topic, extra_args):
    docs = rest("GET", f"docs?user_id=eq.{urllib.parse.quote(uid)}&select=path,content&limit=10000")
    before = {d["path"]: d["content"] for d in docs if safe_path(d["path"])}
    if "schedule.json" not in before:
        return "시간표 없음, 건너뜀"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for p, c in before.items():
            f = root / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(c, encoding="utf-8")
        alarm.BASE_DIR, alarm.PLANS = root, root / "plans"
        os.environ["NTFY_TOPIC"] = topic
        sys.argv = ["alarm.py", "--schedule", str(root / "schedule.json"), *extra_args]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            alarm.main()
        changed = []
        for f in root.rglob("*"):
            if f.is_file():
                p = f.relative_to(root).as_posix()
                c = f.read_text(encoding="utf-8")
                if before.get(p) != c:
                    changed.append({"user_id": uid, "path": p, "content": c})
        if changed:
            rest("POST", "docs?on_conflict=user_id,path", changed, prefer="resolution=merge-duplicates,return=minimal")
        log = out.getvalue()
        if "이미 예약했어요" in log:
            return "이미 예약됨" + (" + 보고서 복습" if "[보고서]" in log else "")
        return f"알림 {log.count('예약 ') + log.count('도착')}개 예약, 저장 {len(changed)}개"


def main():
    extra = [a for a in sys.argv[1:] if a in ("--force",)]
    rows = rest("GET", "docs?path=eq.settings.json&select=user_id,content")
    n = 0
    for i, row in enumerate(rows, 1):
        try:
            topic = (json.loads(row["content"]).get("ntfy_topic") or "").strip()
        except ValueError:
            topic = ""
        if not topic:
            continue
        n += 1
        try:
            print(f"계정 {i}: {run_user(row['user_id'], topic, extra)}")
        except Exception as e:  # 한 계정이 실패해도 다른 계정은 계속
            print(f"계정 {i}: 실패 ({type(e).__name__})")
            traceback.print_exc(limit=0)
    print(f"알림 켜진 계정 {n}개 처리")


if __name__ == "__main__":
    main()
