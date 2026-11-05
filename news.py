#!/usr/bin/env python3
"""구글 뉴스 RSS 에서 분야별 최신 기사 제목·링크를 모아 저장해요.

GitHub Actions(.github/workflows/news.yml)에서 3시간마다 실행돼요.
기사 본문은 저장하지 않고 제목·언론사·시각·링크만 저장해요 (누르면 언론사 기사로 이동).

- docs/news.json            : 최근 기사 (분야마다 최대 RECENT_MAX 개, 처음 모은 시각 `added` 포함)
                              앱은 들어온 지 5시간이 안 된 기사를 📢 공지에서 먼저 보여 주고,
                              5시간이 지나면 📰 뉴스 탭의 다른 기사들과 같이 보여 줘요.
- docs/news/<분야>/<연도>.json : 연도별 기사 보관함 (2000년 ~ 지금, news_archive.py 가 예전 기사를 채워요)
- docs/news/index.json      : 분야·연도별 기사 수 (앱의 연도 고르기용)
"""
import email.utils
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

DOCS = Path(__file__).resolve().parent / "docs"
OUT = DOCS / "news.json"
ARCHIVE = DOCS / "news"
KST = timezone(timedelta(hours=9))
BASE = "https://news.google.com/rss"
TAIL = "hl=ko&gl=KR&ceid=KR:ko"
FIRST_YEAR = 2000


def search_url(q):
    return f"{BASE}/search?q={urllib.parse.quote(q)}&{TAIL}"


# (키, 이름, 최신 기사 주소, 예전 기사 검색어)
CATEGORIES = [
    ("stock", "📈 주식", search_url("주식 OR 증시 OR 코스피 OR 코스닥 when:2d"), "주식 OR 증시 OR 코스피 OR 코스닥"),
    ("economy", "💰 경제", f"{BASE}/headlines/section/topic/BUSINESS?{TAIL}", "경제 OR 금리 OR 물가 OR 환율"),
    ("world", "🌍 세계", f"{BASE}/headlines/section/topic/WORLD?{TAIL}", "국제 OR 외신 OR 정상회담 OR 유엔"),
    ("nation", "🇰🇷 국내", f"{BASE}/headlines/section/topic/NATION?{TAIL}", "사회 OR 사건 OR 교육 OR 날씨"),
    ("politics", "🏛️ 정치", search_url("정치 OR 국회 OR 대통령실 when:2d"), "정치 OR 국회 OR 대통령 OR 청와대"),
    ("rp", "🏦 RP", search_url("RP 환매조건부채권 OR RP금리 OR 발행어음 when:14d"), "RP 환매조건부채권 OR RP금리 OR 발행어음"),
    ("samsung", "🏢 삼성", search_url("삼성전자 OR 삼성 when:2d"), "삼성전자 OR 삼성그룹 OR 삼성"),
    ("nvidia", "🟩 엔비디아", search_url("엔비디아 OR NVIDIA when:3d"), "엔비디아 OR NVIDIA"),
    ("apple", "🍎 애플", search_url("애플 OR 아이폰 OR Apple when:3d"), "애플 OR 아이폰 OR 맥북"),
    ("hynix", "💾 하이닉스", search_url("SK하이닉스 OR 하이닉스 when:3d"), "SK하이닉스 OR 하이닉스 OR 하이닉스반도체"),
    ("lg", "📺 LG", search_url("LG전자 OR LG그룹 OR LG에너지솔루션 OR LG when:3d"), "LG전자 OR LG그룹 OR LG"),
    ("meta", "♾️ 메타", search_url("메타 플랫폼스 OR 페이스북 OR 인스타그램 OR 저커버그 when:3d"), "메타 OR 페이스북 OR 인스타그램 OR 저커버그"),
]
# 구글 뉴스 말고 같이 모으는 곳 (분야 키 → [(주소, 언론사 이름 없을 때 쓸 이름)])
EXTRA_FEEDS = {
    "samsung": [("https://news.samsung.com/kr/feed", "삼성전자 뉴스룸")],
    "nvidia": [("https://nvidianews.nvidia.com/releases.xml", "NVIDIA 뉴스룸")],
    "apple": [("https://www.apple.com/kr/newsroom/rss-feed.rss", "Apple 뉴스룸")],
    "hynix": [("https://news.skhynix.co.kr/feed/", "SK하이닉스 뉴스룸")],
    "lg": [("https://live.lge.co.kr/feed/", "LG전자 LIVE")],
    "meta": [("https://about.fb.com/news/feed/", "Meta 뉴스룸")],
}
PER_FETCH = 40      # 한 번에 받는 최신 기사 수 (분야마다)
RECENT_MAX = 120    # news.json 에 남겨 두는 최근 기사 수 (분야마다)
RECENT_DAYS = 30    # news.json 에는 최근 30일 기사만 (그 전 기사는 연도별 보관함에서)


def now_kst():
    return datetime.now(KST)


def iso(dt):
    return dt.astimezone(KST).isoformat(timespec="minutes")


def fetch(url, tries=3):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (alam news bot)"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(3 * (attempt + 1))


def item_key(x):
    return re.sub(r"\W", "", x["title"])[:40]


def parse(xml_bytes, limit=None, default_source=""):
    root = ET.fromstring(xml_bytes)
    out, seen = [], set()
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if link.endswith("?oc=5"):
            link = link[:-5]
        src_el = it.find("source")
        source = (src_el.text or "").strip() if src_el is not None else default_source
        if source and title.endswith(" - " + source):      # "제목 - 언론사" 에서 언론사 떼기
            title = title[: -len(" - " + source)].strip()
        if not title or not link.lower().startswith(("https://", "http://")):   # javascript: 같은 주소는 버림
            continue
        x = {"title": title[:300], "source": source[:100], "source": source, "time": "", "link": link[:2000]}
        k = item_key(x)
        if k in seen:
            continue
        seen.add(k)
        try:
            x["time"] = iso(email.utils.parsedate_to_datetime(it.findtext("pubDate") or ""))
        except Exception:
            pass
        out.append(x)
    out.sort(key=lambda x: x["time"], reverse=True)
    return out[:limit] if limit else out


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path, data, indent=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))
    path.write_text(text + "\n", encoding="utf-8")


def year_path(key, year):
    return ARCHIVE / key / f"{year}.json"


def add_to_archive(key, items):
    """기사들을 연도별 보관함에 합쳐요 (같은 기사는 한 번만). 새로 들어간 개수를 돌려줘요."""
    by_year = {}
    for x in items:
        y = (x.get("time") or "")[:4]
        if y.isdigit() and int(y) >= FIRST_YEAR:
            by_year.setdefault(int(y), []).append(x)
    added = 0
    for y, xs in by_year.items():
        p = year_path(key, y)
        old = read_json(p, {}).get("items", [])
        keys = {item_key(o) for o in old}
        new = []
        for x in xs:
            k = item_key(x)
            if k not in keys:
                keys.add(k)
                new.append({"title": x["title"], "source": x.get("source", ""), "time": x["time"], "link": x["link"]})
        if not new:
            continue
        added += len(new)
        allx = sorted(old + new, key=lambda o: o["time"], reverse=True)
        write_json(p, {"key": key, "year": y, "items": allx})
    return added


def write_index():
    """docs/news/index.json: 분야·연도별 기사 수"""
    cats = {}
    for key, name, _, _ in CATEGORIES:
        years = {}
        d = ARCHIVE / key
        if d.exists():
            for p in sorted(d.glob("*.json")):
                if p.stem.isdigit():
                    years[p.stem] = len(read_json(p, {}).get("items", []))
        cats[key] = {"name": name, "years": years}
    write_json(ARCHIVE / "index.json", {"updated": iso(now_kst()), "first_year": FIRST_YEAR, "categories": cats}, indent=1)


def main():
    old_data = read_json(OUT, {})
    now = now_kst()
    gap = int(os.environ.get("NEWS_MIN_GAP_MIN", "0") or 0)   # 예약 실행이 몰려도 3시간에 한 번만
    if gap and old_data.get("updated"):
        try:
            if now - datetime.fromisoformat(old_data["updated"]) < timedelta(minutes=gap):
                print(f"마지막 업데이트({old_data['updated']})가 {gap}분이 안 됐어요. 건너뜀")
                return
        except ValueError:
            pass
    old_added = old_data.get("updated") or iso(now)
    old = {c["key"]: c for c in old_data.get("categories", [])}
    cutoff = iso(now - timedelta(days=RECENT_DAYS))
    cats, ok, fresh = [], 0, 0
    for key, name, url, _ in CATEGORIES:
        prev = old.get(key, {}).get("items", [])
        for p in prev:
            p.setdefault("added", old_added)   # 예전 파일 기사는 이미 공지 기간이 지난 것으로
        try:
            got = parse(fetch(url), PER_FETCH)
            ok += 1
            for extra_url, src in EXTRA_FEEDS.get(key, []):
                try:
                    got += parse(fetch(extra_url), PER_FETCH, src)
                except Exception as e:
                    print(f"{key}: {src} 못 받음 ({type(e).__name__})", file=sys.stderr)
        except Exception as e:   # 한 분야가 실패해도 예전 기사는 그대로 둠
            print(f"{key}: 못 받음 ({type(e).__name__})", file=sys.stderr)
            got = []
        merged = {item_key(p): p for p in prev}
        new_here = 0
        for x in got:
            k = item_key(x)
            if k in merged:
                merged[k].update({kk: x[kk] for kk in ("source", "time", "link") if x[kk]})
            else:
                x["added"] = iso(now)
                merged[k] = x
                new_here += 1
        items = [x for x in merged.values() if (x.get("time") or x.get("added", "")) >= cutoff]
        items.sort(key=lambda x: x.get("time") or x.get("added", ""), reverse=True)
        items = items[:RECENT_MAX]
        add_to_archive(key, got)
        fresh += new_here
        cats.append({"key": key, "name": name, "items": items})
        print(f"{key}: 새 기사 {new_here}개 / 최근 {len(items)}개")
    if not ok:
        sys.exit("뉴스를 하나도 못 받았어요")
    write_json(OUT, {"updated": iso(now), "notice_hours": 5, "categories": cats}, indent=1)
    write_index()
    print(f"새 기사 모두 {fresh}개")


if __name__ == "__main__":
    main()
