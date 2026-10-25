# IPTV — 1 playlist, TiviMate ready

Satu file playlist (`iptv.m3u`) berisi channel dari [`iptv-org/iptv`](https://github.com/iptv-org/iptv)
`index.m3u` yang **lolos verifikasi 3 pass** — pass 1 waktu build, pass 2 dan pass 3 diulang
beberapa menit kemudian. Channel yang cuma hidup sesekali / server lemot otomatis dibuang.

```
11.323 stream sumber
  → 4.915 lolos pass 1
  → 3.834 lolos pass 2
  → 3.051 lolos pass 3  ← isi playlist ini (3051 setelah dedupe)
```

Terverifikasi: 25 October 2026

## Pasang di TiviMate

**TiviMate → Settings → Playlists → Add playlist → M3U playlist → masukkan URL:**

```
https://raw.githubusercontent.com/mrdiky71/iptv/main/iptv.m3u
```

Ini **satu-satunya playlist** yang perlu kau pasang. Kategori tetap terpisah rapi di dalam file
lewat `group-title` — di TiviMate muncul sebagai **Groups**:

| Group | Channel |
|---|---|
| 🇮🇩 Indonesia | 96 |
| General | 675 |
| News | 304 |
| 🌐 Other | 272 |
| Religious | 247 |
| Music | 229 |
| Entertainment | 216 |
| Movies | 143 |
| Sports | 101 |
| Kids | 79 |
| Education | 63 |
| Legislative | 57 |
| Culture | 50 |
| Ukraine | 50 |
| _(+19 grup lain, total)_ | 469 |

## Kenapa cuma satu file

TiviMate versi gratis dibatasi 1 playlist. Jadi semua kategori digabung ke satu file dan
dipisah pakai `group-title`, bukan file terpisah. Di TiviMate tinggal buka menu **Groups**
untuk pindah kategori.

## Isi repo

```
iptv.m3u            ← ini yang dipakai (satu-satunya playlist)
extras/tivimate/    arsip 9 bundle per kategori (butuh TiviMate premium)
extras/countries/   arsip 157 file per negara
extras/categories/  arsip 30 file per kategori
extras/dash.m3u     43 stream DASH/MPD (TiviMate nggak bisa MPD)
stats.json          rekap jumlah channel per group
scripts/            verify.py (prober) + one_playlist.py (builder)
```

## Yang perlu diketahui

- **Snapshot, bukan jaminan permanen.** Pass 3 menyaring yang flaky, tapi stream komunitas bisa
  mati kapan saja. Kalau banyak yang mati, jalankan ulang `scripts/`.
- **Bukan playlist berlisensi.** Ini indeks link publik komunitas iptv-org.
- SCTV/RCTI/Indosiar/GTV/MNCTV/Trans TV/Trans 7 **tidak ada versi resmi** — DRM (RCTI+/Vidio/Vision+).
  Yang resmi dari broadcaster: TVRI (semua lokal + World), Metro TV, Nusantara TV, DAAI TV,
  CNN Indonesia, CNBC Indonesia.
- Channel berlabel `[Not 24/7]` memang cuma nyala saat ada siaran.
- Channel `[Geo-blocked]` di source sudah dibuang kalau nggak menjawab dari jaringan build.

## Regenerate

```bash
curl -s https://iptv-org.github.io/iptv/index.m3u | tr -d '\r' > index.m3u
python3 scripts/verify.py urls.txt     # pass 1
python3 scripts/verify.py urls.txt     # pass 2 (opsional, buang yang mati)
python3 scripts/one_playlist.py        # bikin iptv.m3u
```

Sumber data: [iptv-org/database](https://github.com/iptv-org/database) ·
EPG: [iptv-org/epg](https://github.com/iptv-org/epg)
