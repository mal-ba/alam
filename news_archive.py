#!/usr/bin/env python3
"""2000년부터 지난달까지의 예전 뉴스를 분야·반달·검색어마다 구글 뉴스에서 찾아 연도별 보관함에 채워요.

GitHub Actions(.github/workflows/news-archive.yml)에서 분야마다 따로(동시에) 실행돼요.
구글 뉴스는 예전 기간을 검색하면 한 번에 10~30개만 줘요. 기간을 잘게 나눠도(4일씩) 거의 같은 기사만 나와서,
대신 검색어를 하나씩 따로 검색해요 (반달마다 분야별 검색어 8개쯤). 2025년 5월 전반 '경제' 분야로 시험했을 때
"경제 OR 금리 OR …" 한 번은 20개, 검색어 10개를 따로 하면 겹치지 않는 기사 142개였어요.
어디까지 받았는지 docs/news/progress/<분야>.json 에 적어 두고, 다 채운 기간은 다시 안 받아요.

  python news_archive.py                 # 모든 분야 이어서 받기
  python news_archive.py --cat stock     # 주식만
  python news_archive.py --cat stock 2008  # 주식 2008년만
"""
import argparse
import os
import sys
import time
from datetime import date

import news

PROGRESS_DIR = news.ARCHIVE / "progress"
MAX_REQUESTS = int(os.environ.get("MAX_REQUESTS", "1000") or 1000)
MAX_MINUTES = float(os.environ.get("MAX_MINUTES", "300") or 300)
SLEEP = float(os.environ.get("SLEEP", "1.0") or 1.0)
SPLIT = max(1, min(16, int(os.environ.get("SPLIT", "2") or 2)))   # 한 달을 몇 조각으로 나눠 검색할지 (2 = 반달)

# 분야별 예전 기사 검색어 (하나씩 따로 검색). 없는 분야는 news.py 의 검색어를 OR 로 나눠서 써요.
KEYWORDS = {
    "stock": ["주식", "증시", "코스피", "코스닥", "주가", "공모주", "상장", "외국인 순매수"],
    "economy": ["경제", "금리", "물가", "환율", "수출", "부동산", "한국은행", "경기"],
    "world": ["국제", "외신", "정상회담", "유엔", "미국", "중국", "일본", "유럽"],
    "nation": ["사회", "사건", "교육", "날씨", "사고", "경찰", "법원", "지자체"],
    "diplomacy": ["외교", "정상회담", "유엔", "안보리", "외무장관", "국무장관", "한미동맹", "대북"],
    "worldpol": ["미국 대선", "백악관", "총선", "총리", "시진핑", "푸틴", "유럽연합", "일본 총리"],
    "politics": ["정치", "국회", "대통령", "청와대", "여당", "야당", "선거", "국무총리"],
    "sports": ["스포츠", "축구", "야구", "올림픽", "농구", "배구", "골프", "프로야구"],
    "health": ["의학", "의료", "건강", "질병", "신약", "병원", "백신", "암 치료"],
    "science": ["과학", "우주", "연구진", "물리학", "생명과학", "과학기술", "천문", "유전자"],
    "ai": ["인공지능", "AI", "머신러닝", "딥러닝", "챗GPT", "빅데이터", "알파고", "자율주행"],
    "rp": ["RP 환매조건부채권", "RP금리", "발행어음", "CMA"],
    "samsung": ["삼성전자", "삼성그룹", "삼성", "갤럭시", "이건희", "이재용", "삼성SDI", "삼성바이오"],
    "nvidia": ["엔비디아", "NVIDIA", "젠슨 황", "지포스", "GPU"],
    "apple": ["애플", "아이폰", "맥북", "아이패드", "스티브 잡스", "팀 쿡", "애플워치"],
    "hynix": ["SK하이닉스", "하이닉스", "하이닉스반도체", "D램", "HBM", "낸드플래시"],
    "lg": ["LG전자", "LG그룹", "LG", "LG화학", "LG디스플레이", "구광모", "LG에너지솔루션"],
    "meta": ["메타", "페이스북", "인스타그램", "저커버그", "왓츠앱"],
}


def keywords(key, q):
    return KEYWORDS.get(key) or [w.strip() for w in q.split(" OR ") if w.strip()]


def periods(only_year=None):
    """받을 기간 목록 (한 달을 SPLIT 조각으로): 최근 → 예전 순서. 이번 달은 news.py 가 채우니 빼요.
    기간 이름은 "2008-05/8-3" (8조각 중 3번째) 처럼 조각 수가 들어가서, SPLIT 을 바꾸면 새로 받아요."""
    today = date.today()
    y, m = today.year, today.month
    out = []
    while True:
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        if y < news.FIRST_YEAR:
            break
        if only_year is not None and y != only_year:
            continue
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        last = (date(ny, nm, 1) - date(y, m, 1)).days
        starts = [1 + i * last // SPLIT for i in range(SPLIT)]
        bounds = [f"{y}-{m:02d}-{d:02d}" for d in starts] + [f"{ny}-{nm:02d}-01"]
        for i in reversed(range(SPLIT)):
            out.append((f"{y}-{m:02d}/{SPLIT}-{i + 1}", bounds[i], bounds[i + 1]))
    return out


def run_category(key, q, only_year, deadline, budget):
    path = PROGRESS_DIR / f"{key}.json"
    # 예전 방식(검색어를 OR 로 묶어 한 번)으로 받은 기록은 버리고 검색어마다 새로 받기 (이미 모은 기사는 그대로 있어요)
    done = {p for p in news.read_json(path, {}).get("done", []) if "|" in p}
    kws = keywords(key, q)
    todo = [(f"{pid}|{kw}", a, b, kw) for pid, a, b in periods(only_year) for kw in kws]
    todo = [t for t in todo if t[0] not in done]
    print(f"[{key}] 남은 검색 {len(todo)}개 (검색어 {len(kws)}개)")
    reqs, fails, total = 0, 0, 0
    year_new = {}
    for tid, a, b, kw in todo:
        if reqs >= budget or time.time() > deadline:
            break
        reqs += 1
        try:
            items = news.parse(news.fetch(news.search_url(f"{kw} after:{a} before:{b}"), tries=2))
            fails = 0
        except Exception as e:
            fails += 1
            print(f"[{key}] {tid}: 못 받음 ({type(e).__name__})", file=sys.stderr)
            if fails >= 6:          # 계속 막히면 이번엔 그만 (다음 실행에서 이어서)
                print(f"[{key}] 계속 실패해서 이번 실행은 여기까지", file=sys.stderr)
                break
            time.sleep(20 * fails)
            continue
        inside = [x for x in items if a <= x["time"][:10] < b]
        n = news.add_to_archive(key, inside or items)
        total += n
        done.add(tid)
        y = tid[:4]
        year_new[y] = year_new.get(y, 0) + n
        if tid.startswith(f"{y}-01/") and tid.split("|")[0].endswith("-1") and kw == kws[-1]:   # 한 해를 다 받으면 한 줄
            print(f"[{key}] {y}년: 새 기사 {year_new[y]}개")
        if reqs % 40 == 0:   # 중간에 멈춰도 받은 데까지는 남게
            save(path, done, todo)
        time.sleep(SLEEP)
    save(path, done, todo)
    return total, reqs


def save(path, done, todo):
    remain = sum(1 for t in todo if t[0] not in done)
    news.write_json(path, {"updated": news.iso(news.now_kst()), "remaining": remain, "done": sorted(done)}, indent=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cat", default="")
    ap.add_argument("year", nargs="?", type=int)
    args = ap.parse_args()
    cats = [c for c in news.CATEGORIES if not args.cat or c[0] == args.cat]
    if not cats:
        sys.exit(f"없는 분야: {args.cat}")
    deadline = time.time() + MAX_MINUTES * 60
    for key, _, _, q in cats:
        total, reqs = run_category(key, q, args.year, deadline, MAX_REQUESTS)
        print(f"[{key}] 이번에 {reqs}번 검색, 새 기사 {total}개")
    if not args.cat:   # 분야 하나만 받을 땐 index.json 은 마지막 index 작업이 만들어요 (동시에 고치면 충돌)
        news.write_index()


if __name__ == "__main__":
    main()
