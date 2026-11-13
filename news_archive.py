#!/usr/bin/env python3
"""2000년부터 지난달까지의 예전 뉴스를 분야별로 구글 뉴스에서 찾아 연도별 보관함에 채워요.

GitHub Actions(.github/workflows/news-archive.yml)에서 분야마다 따로(동시에) 실행돼요.

구글 뉴스 검색은 한 번에 100개쯤까지만 줘요. 그래서 예전처럼 한 달을 8조각(약 4일)으로 나눠
한 번씩만 검색하면 한 해에 300~500개밖에 안 모였어요 (올해는 3시간마다 모아서 2천~5천 개).
이제는 이렇게 더 많이 모아요.
  1. 검색어를 나눠서도 검색: "주식 OR 증시 OR 코스피 OR 코스닥" 한 번 + "주식", "증시", "코스피", "코스닥" 따로
  2. 기간을 알아서 잘게: 한 달을 검색해서 결과가 꽉 차면(SATURATE 개 이상) 반으로 나눠 다시,
     하루가 될 때까지 계속 나눠요. 결과가 적은 기간(예전 기사)은 적게 검색하고 끝나요.
  3. 한 해에 TARGET_PER_YEAR 개(기본 3000)가 모이면 그 해는 그만 (저장소가 너무 커지지 않게)

어디까지 받았는지 docs/news/progress/<분야>.json 에 "v2:<검색어 번호>:<연-월>" 로 적어 두고,
다 받은 달은 다시 안 받아요. 첫 번째 검색어로 모든 달을 먼저 받고, 그다음 검색어로 다시 모든 달을 받아요
(그래서 중간에 멈춰도 모든 해가 고르게 늘어요).

  python news_archive.py                   # 모든 분야 이어서 받기
  python news_archive.py --cat stock       # 주식만
  python news_archive.py --cat stock 2008  # 주식 2008년만
"""
import argparse
import os
import re
import sys
import time
from datetime import date, timedelta

import news

PROGRESS_DIR = news.ARCHIVE / "progress"
MAX_REQUESTS = int(os.environ.get("MAX_REQUESTS", "6000") or 6000)
MAX_MINUTES = float(os.environ.get("MAX_MINUTES", "300") or 300)
SLEEP = float(os.environ.get("SLEEP", "1.0") or 1.0)
SATURATE = int(os.environ.get("SATURATE", "60") or 60)          # 결과가 이만큼 넘으면 기간을 반으로 나눠 다시 검색
TARGET_PER_YEAR = int(os.environ.get("TARGET_PER_YEAR", "3000") or 3000)
MAX_QUERIES = int(os.environ.get("MAX_QUERIES", "6") or 6)      # 분야마다 검색어 몇 개까지 (합친 것 + 나눈 것)
PREFIX = "v2"


def queries(q):
    """합친 검색어 + OR 로 나눈 검색어 하나하나 ("따옴표 묶음"은 그대로)."""
    parts = [p.strip() for p in re.split(r"\s+OR\s+", q) if p.strip()]
    out = [q] + [p for p in parts if p != q]
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq[:MAX_QUERIES]


def months(only_year=None):
    """받을 달 목록: 지난달 → 2000년 1월 (이번 달은 news.py 가 채워요)."""
    today = date.today()
    y, m = today.year, today.month
    out = []
    while True:
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        if y < news.FIRST_YEAR:
            break
        if only_year is None or y == only_year:
            out.append((y, m))
    return out


def month_bounds(y, m):
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return date(y, m, 1), date(ny, nm, 1)


class Stop(Exception):
    pass


class Runner:
    def __init__(self, key, deadline, budget):
        self.key, self.deadline, self.budget = key, deadline, budget
        self.reqs = self.fails = self.total = 0
        self.year_count = {}

    def count(self, y):
        if y not in self.year_count:
            self.year_count[y] = len(news.read_json(news.year_path(self.key, y), {}).get("items", []))
        return self.year_count[y]

    def search(self, q, a, b):
        """a ≤ 날짜 < b 기간 검색 → (받은 개수, 새로 넣은 개수)"""
        while True:
            if self.reqs >= self.budget or time.time() > self.deadline:
                raise Stop
            self.reqs += 1
            try:
                items = news.parse(news.fetch(news.search_url(f"{q} after:{a} before:{b}"), tries=2))
                self.fails = 0
                break
            except Exception as e:
                self.fails += 1
                print(f"[{self.key}] {q} {a}~{b}: 못 받음 ({type(e).__name__})", file=sys.stderr)
                if self.fails >= 6:   # 계속 막히면 이번엔 그만 (다음 실행에서 이어서)
                    print(f"[{self.key}] 계속 실패해서 이번 실행은 여기까지", file=sys.stderr)
                    raise Stop
                time.sleep(20 * self.fails)
        sa, sb = a.isoformat(), b.isoformat()
        inside = [x for x in items if sa <= x["time"][:10] < sb]
        n = news.add_to_archive(self.key, inside)
        if n:
            self.year_count[a.year] = self.count(a.year) + n
        self.total += n
        time.sleep(SLEEP)
        return len(items), n

    def window(self, q, a, b):
        """기간을 검색하고, 결과가 꽉 찼으면 반으로 나눠서 다시 (하루까지)."""
        got, _ = self.search(q, a, b)
        days = (b - a).days
        if got >= SATURATE and days > 1:
            mid = a + timedelta(days=days // 2)
            self.window(q, a, mid)
            self.window(q, mid, b)


def run_category(key, q, only_year, deadline, budget):
    path = PROGRESS_DIR / f"{key}.json"
    done = {p for p in news.read_json(path, {}).get("done", []) if p.startswith(PREFIX + ":")}
    qs = queries(q)
    todo = [(qi, y, m) for qi in range(len(qs)) for (y, m) in months(only_year)
            if f"{PREFIX}:{qi}:{y}-{m:02d}" not in done]
    print(f"[{key}] 검색어 {len(qs)}개 {qs}, 남은 달 {len(todo)}개")
    r = Runner(key, deadline, budget)
    last_save = 0
    try:
        for qi, y, m in todo:
            pid = f"{PREFIX}:{qi}:{y}-{m:02d}"
            if r.count(y) < TARGET_PER_YEAR:
                a, b = month_bounds(y, m)
                r.window(qs[qi], a, b)
            done.add(pid)
            if r.reqs - last_save >= 100:   # 중간에 멈춰도 받은 데까지는 남게
                save(path, done, todo)
                last_save = r.reqs
    except Stop:
        pass
    save(path, done, todo)
    return r.total, r.reqs


def save(path, done, todo):
    remain = sum(1 for qi, y, m in todo if f"{PREFIX}:{qi}:{y}-{m:02d}" not in done)
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
