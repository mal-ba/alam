#!/usr/bin/env python3
"""2000년부터 지난달까지의 예전 뉴스를 분야·며칠마다 구글 뉴스에서 찾아 연도별 보관함에 채워요.

GitHub Actions(.github/workflows/news-archive.yml)에서 분야마다 따로(동시에) 실행돼요.
구글 뉴스 검색은 한 번에 몇십 개만 주기 때문에 (예전 기간일수록 더 적게) 한 달을 SPLIT 조각(기본 8, 약 4일씩)으로
잘게 나눠서 검색해요. 반달(2조각)씩 검색했을 땐 한 해에 300개쯤밖에 안 모였어요.
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
SPLIT = max(1, min(16, int(os.environ.get("SPLIT", "8") or 8)))   # 한 달을 몇 조각으로 나눠 검색할지


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
    done = {p for p in news.read_json(path, {}).get("done", []) if "/" in p}   # 예전 반달 이름("2008-05a")은 버리고 새로 받기
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
        if pid.startswith(pid[:4] + "-01/") and pid.endswith("-1"):   # 한 해를 다 받으면 한 줄
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
    if not args.cat:   # 분야 하나만 받을 땐 index.json 은 마지막 index 작업이 만들어요 (동시에 고치면 충돌)
        news.write_index()


if __name__ == "__main__":
    main()
