#!/usr/bin/env python3
"""전국 중학교·고등학교 목록(이름·지번주소·도로명주소·위치)을 모아 docs/schools.json 으로 저장해요.

GitHub Actions(.github/workflows/schools.yml)에서 한 달에 한 번 실행돼요.
학교 이름이 같은 학교가 많아서, 앱에서 주소를 보고 정확한 학교를 고르게 하려고 써요.

출처 (아래 순서로 있는 것을 써요)
 0. 공공데이터포털에서 내려받은 '전국초중등학교위치표준데이터' CSV 파일 — python schools.py 파일.csv
    (키 없이 손으로 갱신할 때)
 1. 공공데이터포털 '전국초중등학교위치표준데이터' 오픈API  — GitHub Secret DATA_GO_KR_KEY
    지번주소 + 도로명주소 + 위도·경도
 2. 나이스 교육정보 개방 포털 '학교기본정보'             — GitHub Secret NEIS_KEY
    도로명주소 (지번주소·위치는 없음)

저장 형식 (용량을 줄이려고 배열로)
  {"updated": "...", "source": "...", "fields": [...], "schools": [[id, 이름, 종류, 시도, 지번주소, 도로명주소, 위도, 경도], ...]}
  종류: "중" 또는 "고"
"""
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "docs" / "schools.json"
KST = timezone(timedelta(hours=9))
FIELDS = ["id", "name", "kind", "sido", "jibun", "road", "lat", "lng"]
UA = {"User-Agent": "alam-planner-school-list/1.0"}


def get_json(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read().decode("utf-8", "replace")
            return json.loads(raw)
        except Exception as e:  # 네트워크가 잠깐 끊기면 다시
            if i == tries - 1:
                raise
            print(f"  다시 시도 ({e})", file=sys.stderr)
            time.sleep(3 * (i + 1))


def clean(x):
    return re.sub(r"\s+", " ", str(x or "")).strip()


def kind_of(text):
    t = clean(text)
    if "중학교" in t:
        return "중"
    if "고등학교" in t:
        return "고"
    return ""


def num(x):
    try:
        v = round(float(x), 6)
        return v if v else None
    except (TypeError, ValueError):
        return None


def sido_of(*addrs):
    for a in addrs:
        a = clean(a)
        if a:
            return a.split(" ")[0]
    return ""


# ---------- 1. 공공데이터포털 표준데이터 ----------
def from_data_go_kr(key):
    base = "https://api.data.go.kr/openapi/tn_pubr_public_elesch_mskul_lc_api"
    out, page, rows = [], 1, 1000
    while True:
        q = urllib.parse.urlencode({"serviceKey": key, "pageNo": page, "numOfRows": rows, "type": "json"})
        d = get_json(f"{base}?{q}")
        resp = d.get("response", d)
        head = resp.get("header", {})
        if str(head.get("resultCode", "00")) not in ("00", "0"):
            raise SystemExit(f"공공데이터포털 오류: {head.get('resultCode')} {head.get('resultMsg')}")
        body = resp.get("body", {})
        items = body.get("items") or []
        if isinstance(items, dict):  # {"item": [...]} 형태도 있음
            items = items.get("item") or []
        if isinstance(items, dict):
            items = [items]
        if page == 1:
            print(f"공공데이터포털: 전체 {body.get('totalCount')}개, 항목 예: {sorted(items[0].keys()) if items else '-'}")
        for it in items:
            k = kind_of(it.get("schoolSe") or it.get("schoolNm"))
            if not k:
                continue
            if "폐" in clean(it.get("operSttus")):
                continue
            jibun, road = clean(it.get("lnmadr")), clean(it.get("rdnmadr"))
            sid = clean(it.get("schoolId")) or f"{clean(it.get('schoolNm'))}|{road or jibun}"
            out.append(["D" + sid, clean(it.get("schoolNm")), k, sido_of(jibun, road) or clean(it.get("ctpvOfcdcNm")),
                        jibun, road, num(it.get("latitude")), num(it.get("longitude"))])
        total = int(body.get("totalCount") or 0)
        if not items or page * rows >= total:
            break
        page += 1
    return out, "공공데이터포털 전국초중등학교위치표준데이터"


# ---------- 0. 내려받은 CSV 파일 ----------
def from_csv(path):
    out, ref = [], ""
    with open(path, encoding="utf-8-sig", newline="") as f:
        for it in csv.DictReader(f):
            it = {clean(k).lstrip("\ufeff"): v for k, v in it.items()}
            k = kind_of(it.get("학교급구분") or it.get("학교명"))
            if not k or "폐" in clean(it.get("운영상태")):
                continue
            jibun, road = clean(it.get("소재지지번주소")), clean(it.get("소재지도로명주소"))
            sid = clean(it.get("학교ID")) or f"{clean(it.get('학교명'))}|{road or jibun}"
            out.append(["D" + sid, clean(it.get("학교명")), k, sido_of(jibun, road) or clean(it.get("시도교육청명")),
                        jibun, road, num(it.get("위도")), num(it.get("경도"))])
            ref = max(ref, clean(it.get("데이터기준일자")))
    return out, "공공데이터포털 전국초중등학교위치표준데이터" + (f" (기준일 {ref})" if ref else "")


# ---------- 2. 나이스 학교기본정보 ----------
def from_neis(key):
    base = "https://open.neis.go.kr/hub/schoolInfo"
    out = []
    for kind_nm in ("중학교", "고등학교"):
        page = 1
        while True:
            q = urllib.parse.urlencode({"KEY": key, "Type": "json", "pIndex": page, "pSize": 1000, "SCHUL_KND_SC_NM": kind_nm})
            d = get_json(f"{base}?{q}")
            if "schoolInfo" not in d:
                res = d.get("RESULT", {})
                if res.get("CODE") == "INFO-200":  # 데이터 없음 → 끝
                    break
                raise SystemExit(f"나이스 오류: {res.get('CODE')} {res.get('MESSAGE')}")
            head, body = d["schoolInfo"][0]["head"], d["schoolInfo"][1]["row"]
            total = head[0]["list_total_count"]
            if page == 1:
                print(f"나이스 {kind_nm}: {total}개")
            for it in body:
                road = clean(f"{clean(it.get('ORG_RDNMA'))} {clean(it.get('ORG_RDNDA'))}")
                out.append(["N" + clean(it.get("ATPT_OFCDC_SC_CODE")) + "-" + clean(it.get("SD_SCHUL_CODE")),
                            clean(it.get("SCHUL_NM")), kind_of(kind_nm), clean(it.get("LCTN_SC_NM")) or sido_of(road),
                            "", road, None, None])
            if page * 1000 >= total:
                break
            page += 1
    return out, "나이스 교육정보 개방 포털 학교기본정보"


def main():
    dk, nk = os.environ.get("DATA_GO_KR_KEY", "").strip(), os.environ.get("NEIS_KEY", "").strip()
    if len(sys.argv) > 1:
        schools, source = from_csv(sys.argv[1])
    elif dk:
        schools, source = from_data_go_kr(dk)
    elif nk:
        schools, source = from_neis(nk)
    else:
        # 키가 없으면 지금 있는 docs/schools.json 을 그대로 둠 (CSV 로 손으로 갱신하는 경우)
        print("DATA_GO_KR_KEY·NEIS_KEY 가 없어서 건너뛰어요. 지금 있는 docs/schools.json 을 그대로 써요.")
        return
    # 같은 id 는 하나만, 이름·주소 순 정렬
    seen, uniq = set(), []
    for s in schools:
        if s[0] in seen or not s[1]:
            continue
        seen.add(s[0])
        uniq.append(s)
    uniq.sort(key=lambda s: (s[1], s[3], s[4] or s[5]))
    if len(uniq) < 1000:  # 잘못 받아 와서 목록이 줄어드는 것을 막음
        raise SystemExit(f"학교가 {len(uniq)}개밖에 없어요. 저장하지 않을게요.")
    data = {"updated": datetime.now(KST).strftime("%Y-%m-%d"), "source": source, "fields": FIELDS, "schools": uniq}
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    n_mid = sum(1 for s in uniq if s[2] == "중")
    print(f"저장: 중학교 {n_mid}개, 고등학교 {len(uniq) - n_mid}개 → {OUT.name} ({OUT.stat().st_size // 1024}KB)")


if __name__ == "__main__":
    main()
