#!/usr/bin/env python3
"""2000년부터 지금까지의 예전 뉴스를 분야·달마다 구글 뉴스에서 찾아 연도별 보관함에 채워요.

GitHub Actions(.github/workflows/news-archive.yml)에서 실행돼요.
한 번에 다 받으면 구글이 막을 수 있어서, 실행마다 MAX_REQUESTS 개 달씩 나눠서 받고
어디까지 받았는지 docs/news/progress.json 에 적어 둬요. 다 채우면 아무것도 안 해요.

  python news_archive.py            # 이어서 받기
  python news_archive.py 2008       # 2008년만
"""
import json
import os
import sys
import time
from datetime import date

import news

PROGRESS = news.ARCHIVE / "progress.json"
MAX_REQUESTS = int(os.environ.get("MAX_REQUESTS", "300") or 300)
MAX_MINUTES = float(os.environ.get("MAX_MINUTES", "40") or 40)
SLEEP = 1.2


def months(only_year=None):
    """받을 달 목록: 최근 → 예전 순서 (이번 달은 news.py 가 채우니 빼요)"""
    today = date.today()
    y, m = today.year, today.month
    out = []
    while y >= news.FIRST_YEAR:
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        if y < news.FIRST_YEAR:
            break
        if only_year is None or y == only_year:
            out.append((y, m))
    return out


def month_range(y, m):
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y}-{m:02d}-01", f"{ny}-{nm:02d}-01"


def main():
    only_year = int(sys.argv[1]) if len(sys.argv) > 1 else None
    prog = news.read_json(PROGRESS, {})
    done = set(prog.get("done", []))
    todo = [(key, q, y, m) for (y, m) in months(only_year) for key, _, _, q in news.CATEGORIES
            if f"{key}:{y}-{m:02d}" not in done]
    print(f"남은 달: {len(todo)}개 (이번 실행: 최대 {MAX_REQUESTS}개)")
    start, reqs, fails, total = time.time(), 0, 0, 0
    for key, q, y, m in todo:
        if reqs >= MAX_REQUESTS or time.time() - start > MAX_MINUTES * 60:
            break
        a, b = month_range(y, m)
        reqs += 1
        try:
            items = news.parse(news.fetch(news.search_url(f"{q} after:{a} before:{b}"), tries=2))
            fails = 0
        except Exception as e:
            fails += 1
            print(f"{key} {y}-{m:02d}: 못 받음 ({type(e).__name__})", file=sys.stderr)
            if fails >= 5:          # 계속 막히면 이번엔 그만 (다음 실행에서 이어서)
                print("계속 실패해서 이번 실행은 여기까지", file=sys.stderr)
                break
            time.sleep(30)
            continue
        items = [x for x in items if a <= x["time"][:10] < b] or items
        n = news.add_to_archive(key, items)
        total += n
        done.add(f"{key}:{y}-{m:02d}")
        print(f"{key} {y}-{m:02d}: {len(items)}개 (새로 {n})")
        time.sleep(SLEEP)
    remain = len(todo) - sum(1 for key, _, y, m in todo if f"{key}:{y}-{m:02d}" in done)
    news.write_json(PROGRESS, {"updated": news.iso(news.now_kst()), "remaining": remain,
                               "done": sorted(done)}, indent=0)
    news.write_index()
    print(f"이번에 새로 넣은 기사 {total}개, 남은 달 {remain}개")


if __name__ == "__main__":
    main()
