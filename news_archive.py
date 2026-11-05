#!/usr/bin/env python3
"""2000년부터 지난달까지의 예전 뉴스를 분야·반달마다 구글 뉴스에서 찾아 연도별 보관함에 채워요.

GitHub Actions(.github/workflows/news-archive.yml)에서 분야마다 따로(동시에) 실행돼요.
구글 뉴스 검색은 한 번에 최대 100개쯤만 주기 때문에 기간을 반달씩 잘게 나눠서 검색해요.
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


def periods(only_year=None):
    """받을 기간 (반달) 목록: 최근 → 예전 순서. 이번 달은 news.py 가 채우니 빼요."""
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
        mid = f"{y}-{m:02d}-16"
        out.append((f"{y}-{m:02d}b", mid, f"{ny}-{nm:02d}-01"))
        out.append((f"{y}-{m:02d}a", f"{y}-{m:02d}-01", mid))
    return out


def run_category(key, q, only_year, deadline, budget):
    path = PROGRESS_DIR / f"{key}.json"
    done = set(news.read_json(path, {}).get("done", []))
    todo = [p for p in periods(only_year) if p[0] not in done]
    print(f"[{key}] 남은 기간 {len(todo)}개")
    reqs, fails, total = 0, 0, 0
    year_new = {}
    for pid, a, b in todo:
        if reqs >= budget or time.time() > deadline:
            break
        reqs += 1
        try:
            items = news.parse(news.fetch(news.search_url(f"{q} after:{a} before:{b}"), tries=2))
            fails = 0
        except Exception as e:
            fails += 1
            print(f"[{key}] {pid}: 못 받음 ({type(e).__name__})", file=sys.stderr)
            if fails >= 6:          # 계속 막히면 이번엔 그만 (다음 실행에서 이어서)
                print(f"[{key}] 계속 실패해서 이번 실행은 여기까지", file=sys.stderr)
                break
            time.sleep(20 * fails)
            continue
        inside = [x for x in items if a <= x["time"][:10] < b]
        n = news.add_to_archive(key, inside or items)
        total += n
        done.add(pid)
        year_new[pid[:4]] = year_new.get(pid[:4], 0) + n
        if pid.endswith("01a"):   # 한 해를 다 받으면 한 줄
            print(f"[{key}] {pid[:4]}년: 새 기사 {year_new[pid[:4]]}개")
        if reqs % 40 == 0:   # 중간에 멈춰도 받은 데까지는 남게
            save(path, done, todo)
        time.sleep(SLEEP)
    save(path, done, todo)
    return total, reqs


def save(path, done, todo):
    remain = sum(1 for p in todo if p[0] not in done)
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
    news.write_index()


if __name__ == "__main__":
    main()
