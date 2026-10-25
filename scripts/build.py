#!/usr/bin/env python3
"""Build the split playlist repo tree from index_lf.m3u filtered by alive_urls.txt."""
import json, os, re, shutil, urllib.request
from collections import defaultdict

SRC = "/tmp/index_lf.m3u"
ALIVE = "/tmp/alive_urls.txt"
DASH = "/tmp/dash_urls.txt"
OUT = "/tmp/iptv-build"

alive = {l.strip() for l in open(ALIVE) if l.strip()}
dash = {l.strip() for l in open(DASH) if l.strip()} if os.path.exists(DASH) else set()

raw = open(SRC, encoding="utf-8-sig").read()
lines = raw.split("\n")
header, blocks, cur = "", [], []
for ln in lines:
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

def attrs_of(b):
    return {k.lower(): v for k, v in ATTR.findall(b[0].split(",", 1)[0])}

live_blocks, dash_blocks, seen = [], [], set()
for b in blocks:
    u = b[-1]
    if u in seen:
        continue
    if u in dash:
        seen.add(u)
        dash_blocks.append(b)
    elif u in alive:
        seen.add(u)
        live_blocks.append(b)

print(f"source {len(blocks)} blocks | alive {len(live_blocks)} | dash {len(dash_blocks)}")

with urllib.request.urlopen("https://iptv-org.github.io/api/countries.json") as r:
    countries = json.load(r)
cc_name = {c["code"].lower(): c["name"] for c in countries}

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "x"

if os.path.exists(OUT):
    shutil.rmtree(OUT)
for d in ("countries", "categories", "tivimate"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

def write(path, blks):
    with open(path, "w", encoding="utf-8") as f:
        f.write((header or "#EXTM3U") + "\n")
        for b in blks:
            f.write("\n" + "\n".join(b) + "\n")

by_country, by_cat, unknown = defaultdict(list), defaultdict(list), []
for b in live_blocks:
    a = attrs_of(b)
    tid = a.get("tvg-id", "")
    cc = ""
    if tid:
        base = tid.split("@")[0]
        if "." in base:
            c = base.rsplit(".", 1)[1].lower()
            if len(c) == 2 and c.isalpha():
                cc = c
    (by_country[cc] if cc else defaultdict(list))  # noqa
    if cc:
        by_country[cc].append(b)
    else:
        unknown.append(b)
    for cat in [x.strip() for x in a.get("group-title", "").split(";") if x.strip()]:
        by_cat[cat].append(b)

write(os.path.join(OUT, "index.m3u"), live_blocks)
write(os.path.join(OUT, "dash.m3u"), dash_blocks)
for cc, blks in sorted(by_country.items()):
    name = cc_name.get(cc, cc)
    write(os.path.join(OUT, "countries", f"{cc}-{slug(name)}.m3u"), blks)
if unknown:
    write(os.path.join(OUT, "countries", "unknown.m3u"), unknown)
for cat, blks in sorted(by_cat.items()):
    write(os.path.join(OUT, "categories", f"{slug(cat)}.m3u"), blks)

bundles = {
    "01-indonesia": by_country.get("id", []),
    "02-news": by_cat.get("News", []),
    "03-sports": by_cat.get("Sports", []),
    "04-movies": by_cat.get("Movies", []),
    "05-kids": by_cat.get("Kids", []),
    "06-entertainment": by_cat.get("Entertainment", []),
    "07-music": by_cat.get("Music", []),
    "08-documentary": by_cat.get("Documentary", []),
    "99-all-channels": live_blocks,
}
for n, blks in bundles.items():
    write(os.path.join(OUT, "tivimate", f"{n}.m3u"), blks)

stats = {
    "total_source": len(blocks),
    "alive_total": len(live_blocks),
    "dash_total": len(dash_blocks),
    "countries": {cc: len(v) for cc, v in sorted(by_country.items(), key=lambda x: -len(x[1]))},
    "categories": {k: len(v) for k, v in sorted(by_cat.items(), key=lambda x: -len(x[1]))},
    "bundles": {k: len(v) for k, v in bundles.items()},
}
json.dump(stats, open("/tmp/stats.json", "w"), indent=2, ensure_ascii=False)
print(json.dumps(stats["bundles"], indent=0))
print("top countries:", list(stats["countries"].items())[:8])
print("files:", len(os.listdir(os.path.join(OUT, "countries"))), "countries,",
      len(os.listdir(os.path.join(OUT, "categories"))), "categories")
