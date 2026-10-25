#!/usr/bin/env python3
"""Build ONE TiviMate playlist from the stable (3-pass) URL set.

Grouping: Indonesian channels -> "Indonesia", others -> first original group-title
(fallback: country name). Dedupe by tvg-id so one channel appears once.
"""
import json, re, urllib.request
from collections import defaultdict

SRC = "/tmp/index_lf.m3u"
ALIVE = "/tmp/alive_urls.txt"
OUT = "/tmp/iptv-single/iptv.m3u"

alive = {l.strip() for l in open(ALIVE) if l.strip()}

raw = open(SRC, encoding="utf-8-sig").read()
header, blocks, cur = "", [], []
for ln in raw.split("\n"):
    if not ln.strip():
        continue
    if ln.startswith("#EXTM3U"):
        header = ln.strip()
        continue
    if ln.startswith("#"):
        cur.append(ln.strip())
        continue
    cur.append(ln.strip())
    blocks.append(cur)
    cur = []

ATTR = re.compile(r'([a-zA-Z0-9_-]+)="([^"]*)"')

with urllib.request.urlopen("https://iptv-org.github.io/api/countries.json") as r:
    cc_name = {c["code"].lower(): c["name"] for c in json.load(r)}

sel, seen_url, seen_id = [], set(), set()
skipped_dup = 0
for b in blocks:
    u = b[-1]
    if u not in alive or u in seen_url:
        continue
    a = {k.lower(): v for k, v in ATTR.findall(b[0].split(",", 1)[0])}
    tid = a.get("tvg-id", "").strip()
    cc = ""
    if "." in tid.split("@")[0]:
        c = tid.split("@")[0].rsplit(".", 1)[1].lower()
        if len(c) == 2 and c.isalpha():
            cc = c
    title = b[0].split(",", 1)[-1]
    key = tid or title.lower()
    if key in seen_id:
        skipped_dup += 1
        continue
    seen_id.add(key)
    seen_url.add(u)

    if cc == "id":
        group = "🇮🇩 Indonesia"
    else:
        g = [x.strip() for x in a.get("group-title", "").split(";") if x.strip()]
        g = [x for x in g if x.lower() not in ("undefined", "")]
        group = g[0] if g else (cc_name.get(cc, "Other") if cc else "Other")

    line = re.sub(r'group-title="[^"]*"', f'group-title="{group}"', b[0])
    if 'group-title=' not in line:
        line = line.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{group}"', 1)
    sel.append([line] + b[1:])

# grup kecil digabung biar enak dinavigasi pakai remote
MIN = 15
cnt = defaultdict(int)
for b in sel:
    cnt[re.search(r'group-title="([^"]*)"', b[0]).group(1)] += 1
merged = 0
for b in sel:
    old = re.search(r'group-title="([^"]*)"', b[0]).group(1)
    if cnt[old] < MIN and old != "🇮🇩 Indonesia":
        b[0] = re.sub(r'group-title="[^"]*"', 'group-title="🌐 Other"', b[0])
        merged += 1

order = {"🇮🇩 Indonesia": 0, "🌐 Other": 99}


def rank(blk):
    g = re.search(r'group-title="([^"]*)"', blk[0]).group(1)
    return (order.get(g, 1), g.lower(), blk[0].split(",", 1)[-1].lower())


sel.sort(key=rank)
import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for b in sel:
        f.write("\n" + "\n".join(b) + "\n")

groups = defaultdict(int)
for b in sel:
    groups[re.search(r'group-title="([^"]*)"', b[0]).group(1)] += 1
print(f"stable alive {len(alive)} -> written {len(sel)} (dup dibuang {skipped_dup})")
print("grup:", len(groups))
for g, n in sorted(groups.items(), key=lambda x: -x[1])[:12]:
    print(f"  {n:4}  {g}")
json.dump({"total": len(sel), "groups": dict(groups)}, open("/tmp/stats_single.json", "w"),
          indent=2, ensure_ascii=False)
