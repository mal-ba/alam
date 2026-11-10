#!/usr/bin/env python3
"""💬 커뮤니티 피드 만들기 (GitHub Actions 에서 몇 분마다 실행).

앱에서 올린 게시물은 각자 자기 Supabase 칸(docs 표, 경로 community/posts/<번호>.json)에 저장돼요.
다른 사람 칸은 앱에서 못 읽으니(행 단위 보안), 이 스크립트가 비밀 키로 모두의 게시물을 모아
Supabase Storage 의 공개 버킷 `community` 에 피드(feed.json)와 사진으로 올려요.
버킷이 없으면 처음 실행할 때 알아서 만들어요 → SQL 이나 대시보드에서 따로 할 일이 없어요.

🔒 비밀번호를 건 게시물은 앱(브라우저)에서 비밀번호로 암호화(AES-GCM)한 내용만 올라가요.
   원래 글·사진·열쇠(key)는 피드에 절대 넣지 않아요.
공개 저장소라 Actions 로그는 누구나 봐요 → 게시물 내용·계정은 찍지 않고 개수만 찍어요.

환경변수: SUPABASE_URL, SUPABASE_SERVICE_KEY (GitHub Secrets)
"""
import base64
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
if not re.fullmatch(r"https://[a-z0-9-]+\.supabase\.co", URL):   # 키를 엉뚱한 곳으로 보내지 않게
    sys.exit("SUPABASE_URL 은 https://<프로젝트>.supabase.co 형식이어야 해요")

BUCKET = "community"
PREFIX = "community/posts/"
CID_RE = re.compile(r"[a-z0-9]{6,32}")
B64_RE = re.compile(r"[A-Za-z0-9+/=]+")
MAX_PER_USER, MAX_POSTS = 100, 500
MAX_TEXT, MAX_NICK, MAX_IMAGES = 2000, 20, 4
MAX_IMAGE_BYTES, MAX_ENC_BYTES = 1_000_000, 2_000_000
IMAGE_TYPES = {b"\xff\xd8\xff": ("image/jpeg", "jpg"), b"\x89PNG": ("image/png", "png"), b"RIFF": ("image/webp", "webp")}


def request(method, url, body=None, ctype="application/json", headers=None):
    data = body if isinstance(body, (bytes, type(None))) else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header("apikey", KEY)
    if not KEY.startswith("sb_secret_"):   # 예전 service_role(JWT) 키만 Authorization 에도 넣음
        req.add_header("Authorization", f"Bearer {KEY}")
    if data is not None:
        req.add_header("Content-Type", ctype)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    return json.loads(raw) if raw and r.headers.get_content_type() == "application/json" else raw


def storage(method, path, body=None, ctype="application/json", headers=None):
    return request(method, f"{URL}/storage/v1/{path}", body, ctype, headers)


def ensure_bucket():
    try:
        storage("GET", f"bucket/{BUCKET}")
        return
    except urllib.error.HTTPError as e:
        if e.code not in (400, 404):
            raise
    storage("POST", "bucket", {"id": BUCKET, "name": BUCKET, "public": True, "file_size_limit": MAX_ENC_BYTES,
                               "allowed_mime_types": ["application/json", "image/jpeg", "image/png", "image/webp"]})
    print("공개 버킷 community 를 만들었어요")


def list_objects(folder):
    out, offset = [], 0
    while True:
        rows = storage("POST", f"object/list/{BUCKET}", {"prefix": folder, "limit": 1000, "offset": offset}) or []
        out += [f"{folder}/{r['name']}" for r in rows if r.get("id")]
        if len(rows) < 1000:
            return out
        offset += 1000


def upload(name, data, ctype, cache="31536000"):
    storage("POST", f"object/{BUCKET}/{name}", data, ctype, {"x-upsert": "true", "cache-control": f"max-age={cache}"})


def fetch_posts():
    rows, offset = [], 0
    while True:
        q = f"docs?path=like.{urllib.parse.quote(PREFIX)}*&select=user_id,path,content&order=updated_at.desc&limit=200&offset={offset}"
        page = request("GET", f"{URL}/rest/v1/{q}")
        rows += page
        if len(page) < 200:
            return rows
        offset += 200


def clean_text(s, n):
    s = str(s or "").replace("\r\n", "\n")
    s = "".join(ch for ch in s if ch in "\n\t" or ord(ch) >= 32)
    return s.strip()[:n]


def decode_image(data_url):
    m = re.fullmatch(r"data:image/(?:jpeg|png|webp);base64,([A-Za-z0-9+/=]+)", str(data_url or ""))
    if not m:
        return None
    raw = base64.b64decode(m.group(1))
    if len(raw) > MAX_IMAGE_BYTES:
        return None
    for magic, kind in IMAGE_TYPES.items():
        if raw.startswith(magic) and (magic != b"RIFF" or raw[8:12] == b"WEBP"):
            return raw, kind
    return None


def iso(s):
    return s if isinstance(s, str) and re.fullmatch(r"\d{4}-\d\d-\d\dT[\d:.]+Z", s) else None


def build():
    ensure_bucket()
    per_user, posts, files = {}, [], {}   # files: 버킷 이름 → (bytes, 형식)
    skipped = 0
    for row in fetch_posts():
        uid, path = row["user_id"], row["path"]
        cid = path[len(PREFIX):].removesuffix(".json")
        if not CID_RE.fullmatch(cid) or per_user.get(uid, 0) >= MAX_PER_USER:
            skipped += 1
            continue
        try:
            d = json.loads(row["content"])
            assert isinstance(d, dict) and d.get("cid") == cid
        except Exception:
            skipped += 1
            continue
        per_user[uid] = per_user.get(uid, 0) + 1
        # 계정 번호는 드러내지 않고, 앱이 '내 글'인지 알아볼 수 있게 sha256(계정:번호) 앞 16자리
        pid = hashlib.sha256(f"{uid}:{cid}".encode()).hexdigest()[:16]
        post = {"id": pid, "nickname": clean_text(d.get("nickname"), MAX_NICK) or "익명",
                "created": iso(d.get("created")), "updated": iso(d.get("updated"))}
        if not post["created"]:
            skipped += 1
            continue
        if d.get("lock"):
            enc = d.get("enc") or {}
            parts = [enc.get(k) for k in ("salt", "iv", "data")]
            if not all(isinstance(x, str) and B64_RE.fullmatch(x) for x in parts) or sum(map(len, parts)) > MAX_ENC_BYTES:
                skipped += 1
                continue
            blob = json.dumps({"v": 1, "salt": parts[0], "iv": parts[1], "data": parts[2]}).encode()
            name = f"e/{pid}-{hashlib.sha256(blob).hexdigest()[:10]}.json"
            files[name] = (blob, "application/json")
            post.update(lock=True, enc=name)   # 🔒 원래 글·사진·key 는 절대 안 넣어요
        else:
            imgs = []
            for i, u in enumerate((d.get("images") or [])[:MAX_IMAGES]):
                got = decode_image(u)
                if got:
                    raw, (ctype, ext) = got
                    name = f"p/{pid}-{i}-{hashlib.sha256(raw).hexdigest()[:10]}.{ext}"
                    files[name] = (raw, ctype)
                    imgs.append(name)
            text = clean_text(d.get("text"), MAX_TEXT)
            if not text and not imgs:
                skipped += 1
                continue
            post.update(lock=False, text=text, images=imgs)
        posts.append(post)

    posts.sort(key=lambda p: p["created"], reverse=True)
    posts = posts[:MAX_POSTS]
    keep = {p["enc"] for p in posts if p["lock"]} | {n for p in posts if not p["lock"] for n in p["images"]}

    existing = set(list_objects("p") + list_objects("e"))
    new = [n for n in keep if n not in existing]
    for n in new:   # 이름에 내용 해시가 들어 있어서 바뀐 것만 올라가요
        upload(n, *files[n])
    gone = sorted(existing - keep)
    for i in range(0, len(gone), 100):   # 지운 게시물의 사진·암호문도 지워요
        storage("DELETE", f"object/{BUCKET}", {"prefixes": gone[i:i + 100]})

    feed = {"v": 1, "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "posts": posts}
    upload("feed.json", json.dumps(feed, ensure_ascii=False, separators=(",", ":")).encode(), "application/json", cache="30")
    print(f"게시물 {len(posts)}개 (계정 {len(per_user)}개), 새 파일 {len(new)}개, 지운 파일 {len(gone)}개, 건너뜀 {skipped}개")


if __name__ == "__main__":
    try:
        build()
    except urllib.error.HTTPError as e:   # 응답 본문엔 내용이 섞일 수 있어서 상태 코드만
        sys.exit(f"Supabase 요청 실패: HTTP {e.code}")
