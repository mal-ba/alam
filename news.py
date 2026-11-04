#!/usr/bin/env python3
"""구글 뉴스 RSS 에서 분야별 최신 기사 제목·링크를 모아 docs/news.json 으로 저장해요.

GitHub Actions(.github/workflows/news.yml)에서 몇 시간마다 실행돼요.
기사 본문은 저장하지 않고 제목·언론사·시각·링크만 저장해요 (누르면 언론사 기사로 이동).
"""
import email.utils
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "docs" / "news.json"
KST = timezone(timedelta(hours=9))
BASE = "https://news.google.com/rss"
TAIL = "hl=ko&gl=KR&ceid=KR:ko"

# (키, 이름, 주소)
CATEGORIES = [
    ("stock", "📈 주식", f"{BASE}/search?q={urllib.parse.quote('주식 OR 증시 OR 코스피 OR 코스닥 when:2d')}&{TAIL}"),
    ("economy", "💰 경제", f"{BASE}/headlines/section/topic/BUSINESS?{TAIL}"),
    ("world", "🌍 세계", f"{BASE}/headlines/section/topic/WORLD?{TAIL}"),
    ("nation", "🇰🇷 국내", f"{BASE}/headlines/section/topic/NATION?{TAIL}"),
    ("politics", "🏛️ 정치", f"{BASE}/search?q={urllib.parse.quote('정치 OR 국회 OR 대통령실 when:2d')}&{TAIL}"),
    ("rp", "🏦 RP", f"{BASE}/search?q={urllib.parse.quote('RP 환매조건부채권 OR RP금리 OR 발행어음 when:14d')}&{TAIL}"),
]
PER_CATEGORY = 30


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (alam news bot)"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))


def parse(xml_bytes):
    root = ET.fromstring(xml_bytes)
    out, seen = [], set()
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        src_el = it.find("source")
        source = (src_el.text or "").strip() if src_el is not None else ""
        if source and title.endswith(" - " + source):      # "제목 - 언론사" 에서 언론사 떼기
            title = title[: -len(" - " + source)].strip()
        if not title or not link:
            continue
        key = re.sub(r"\W", "", title)[:40]
        if key in seen:
            continue
        seen.add(key)
        try:
            ts = email.utils.parsedate_to_datetime(it.findtext("pubDate") or "").astimezone(KST).isoformat(timespec="minutes")
        except Exception:
            ts = ""
        out.append({"title": title, "source": source, "time": ts, "link": link})
    out.sort(key=lambda x: x["time"], reverse=True)
    return out[:PER_CATEGORY]


def main():
    old = {}
    if OUT.exists():
        try:
            old = {c["key"]: c for c in json.loads(OUT.read_text(encoding="utf-8")).get("categories", [])}
        except Exception:
            old = {}
    cats, ok = [], 0
    for key, name, url in CATEGORIES:
        try:
            items = parse(fetch(url))
            ok += 1
        except Exception as e:   # 한 분야가 실패해도 예전 기사는 그대로 둠
            print(f"{key}: 못 받음 ({type(e).__name__})", file=sys.stderr)
            items = old.get(key, {}).get("items", [])
        cats.append({"key": key, "name": name, "items": items})
        print(f"{key}: {len(items)}개")
    if not ok:
        sys.exit("뉴스를 하나도 못 받았어요")
    data = {"updated": datetime.now(KST).isoformat(timespec="minutes"), "categories": cats}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
