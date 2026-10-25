#!/usr/bin/env python3
"""Verify every URL in an M3U: HTTP ok + real bytes (HLS variant/segment, DASH MPD, direct)."""
import concurrent.futures
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urljoin

ATTR_RE = re.compile(r'([a-zA-Z0-9_-]+)="([^"]*)"')
DEFAULT_UA = "VLC/3.0.20 LibVLC/3.0.20"
CAP = 32768
OK_CODES = {"200", "206", "301", "302"}
lock = threading.Lock()


def load_meta(path):
    raw = open(path, encoding="utf-8-sig").read().replace("\r\n", "\n").replace("\r", "\n")
    meta, cur = {}, []
    for ln in raw.split("\n"):
        if not ln.strip() or ln.startswith("#EXTM3U"):
            continue
        if ln.startswith("#"):
            cur.append(ln.strip())
            continue
        cur.append(ln.strip())
        attrs = {k.lower(): v for k, v in ATTR_RE.findall(cur[0])}
        ua = attrs.get("http-user-agent") or DEFAULT_UA
        ref = attrs.get("http-referrer") or attrs.get("http-referer") or ""
        for l in cur[1:-1]:
            low = l.lower()
            if low.startswith("#extvlcopt:http-user-agent="):
                ua = l.split("=", 1)[1].strip()
            elif low.startswith("#extvlcopt:http-referrer=") or low.startswith("#extvlcopt:http-referer="):
                ref = l.split("=", 1)[1].strip()
        meta[cur[-1]] = (ua, ref)
        cur = []
    return meta


def curl(url, ua, ref, timeout=10):
    fd, path = tempfile.mkstemp(prefix="vb_", dir="/tmp")
    os.close(fd)
    parts = ["curl", "-sL", "-m", str(timeout), "--connect-timeout", "6",
             "-A", ua or DEFAULT_UA, "--compressed",
             "-o", path, "-w", "%{http_code}", url]
    if ref:
        parts = parts[:-1] + ["-e", ref, url]
    cmd = " ".join(shlex.quote(p) for p in parts)
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout + 8)
        code = p.stdout.decode("ascii", "ignore").strip()
        body = b""
        try:
            with open(path, "rb") as fh:
                body = fh.read(CAP)
        except OSError:
            pass
        return code, body
    except Exception:
        return "", b""
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def is_playlist(b):
    h = b.lstrip()[:400]
    return h.startswith(b"#EXT") or b"#EXTM3U" in h


def verify(url):
    ua, ref = META.get(url, (DEFAULT_UA, ""))
    code, body = curl(url, ua, ref)
    if code not in OK_CODES:
        return False, f"http {code or 'fail'}"
    if not body:
        return False, "empty"

    if is_playlist(body):
        target, cur = url, body
        for _ in range(3):
            lines = [l.strip() for l in cur.decode("utf-8", "ignore").splitlines()
                     if l.strip() and not l.startswith("#")]
            if not lines:
                return False, "empty playlist"
            target = urljoin(target, lines[0])
            c2, cur = curl(target, ua, ref, 12)
            if c2 not in OK_CODES or not cur:
                return False, f"seg http {c2 or 'fail'}"
            if not is_playlist(cur):
                n = len(cur)
                return (n > 2000), (f"seg {n}B" if n > 2000 else f"seg short {n}B")
        return False, "nesting"

    low = body[:800].lower()
    if b"<mpd" in low:
        return True, "dash"
    if low.lstrip().startswith(b"<?xml") or b"<html" in low or b"<!doctype" in low:
        return False, "html/xml"
    n = len(body)
    return (n > 2000), (f"direct {n}B" if n > 2000 else f"direct short {n}B")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/urls.txt"
    urls = [l.strip() for l in open(src, encoding="utf-8", errors="ignore") if l.strip()]
    print(f"verifying {len(urls)} urls", flush=True)
    META = load_meta("/tmp/index_lf.m3u")
    t0 = time.time()
    res, done = {}, [0]

    def work(u):
        r = verify(u)
        with lock:
            res[u] = r
            done[0] += 1
            if done[0] % 500 == 0:
                a = sum(1 for v in res.values() if v[0])
                print(f"  {done[0]}/{len(urls)} alive={a} {int(time.time()-t0)}s", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get("W", "120"))) as ex:
        list(ex.map(work, urls))

    alive = [u for u in urls if res[u][0]]
    dash = [u for u in alive if res[u][1] == "dash"]
    json.dump({u: list(v) for u, v in res.items()}, open("/tmp/verify_result.json", "w"), indent=0)
    open("/tmp/alive_urls.txt", "w").write("\n".join(alive) + "\n")
    open("/tmp/dash_urls.txt", "w").write("\n".join(dash) + "\n")
    print(f"DONE alive {len(alive)}/{len(urls)} (dash {len(dash)}) in {int(time.time()-t0)}s", flush=True)
