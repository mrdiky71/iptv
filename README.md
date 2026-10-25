# IPTV Playlists — verified played-only (TiviMate ready)

Playlist hasil filter dari [`iptv-org/iptv`](https://github.com/iptv-org/iptv) `index.m3u`.
Setiap stream sudah dites **level-3** (bukan cuma HTTP 200): master/variant HLS di-resolve
sampai segmen pertama benar-benar mengeluarkan bytes video (>2 KB). Yang mati, 404, 403,
HTML error page, atau cuma balas 188 byte dibuang.

```
11.323 stream sumber  →  4.958 lolos tes  →  4.915 unik di playlist  (+43 DASH dipisah)
```

Terverifikasi: 25 October 2026

## Pakai di TiviMate

TiviMate → **Settings → Playlists → Add playlist → M3U playlist** → paste URL `raw` di bawah.

| Bundle | Channel | URL |
|---|---|---|
| 🇮🇩 Indonesia | 104 | `https://raw.githubusercontent.com/mrdiky71/iptv/main/tivimate/01-indonesia.m3u` |
| 📰 News | 536 | `https://raw.githubusercontent.com/mrdiky71/iptv/main/tivimate/02-news.m3u` |
| ⚽ Sports | 161 | `https://raw.githubusercontent.com/mrdiky71/iptv/main/tivimate/03-sports.m3u` |
| 🎬 Movies | 237 | `https://raw.githubusercontent.com/mrdiky71/iptv/main/tivimate/04-movies.m3u` |
| 🧸 Kids | 140 | `https://raw.githubusercontent.com/mrdiky71/iptv/main/tivimate/05-kids.m3u` |
| 🎭 Entertainment | 350 | `https://raw.githubusercontent.com/mrdiky71/iptv/main/tivimate/06-entertainment.m3u` |
| 🎵 Music | 397 | `https://raw.githubusercontent.com/mrdiky71/iptv/main/tivimate/07-music.m3u` |
| 🔍 Documentary | 80 | `https://raw.githubusercontent.com/mrdiky71/iptv/main/tivimate/08-documentary.m3u` |
| 🌍 Semua | 4915 | `https://raw.githubusercontent.com/mrdiky71/iptv/main/tivimate/99-all-channels.m3u` |

**Saran:** jangan load `99-all-channels` bareng-bareng bundle lain di TiviMate — channel-nya
dobel dan bikin berat. Pilih satu gaya: semua-sekaligus, atau per-kategori.

## Struktur

```
tivimate/          bundle siap tempel di TiviMate (8 kategori + all)
countries/         157 file per negara, nama file = kode-negara-nama
categories/        30 file per kategori (News, Sports, Movies, ...)
index.m3u          4.915 channel unik, satu file
dash.m3u           43 stream DASH/MPD — TiviMate umumnya nggak bisa, dipisah biar nggak ganggu
stats.json         jumlah channel per negara/kategori/bundle
```

URL per negara contoh: `https://raw.githubusercontent.com/mrdiky71/iptv/main/countries/id-indonesia.m3u`

## Yang perlu diketahui

- **Bukan playlist berlisensi.** Ini indeks link publik dari komunitas iptv-org. Stream yang
  hidup ≠ stream yang legal. Restream channel premium (BeIN, pay TV) statusnya tidak berizin.
- **SCTV, RCTI, Indosiar, GTV, MNCTV, Trans TV/7 tidak ada versi resminya** — DRM (RCTI+/Vidio/Vision+).
  Yang stabil dari broadcaster sendiri: TVRI (semua lokal + World/Sport), Metro TV, tvOne, Kompas TV,
  iNews, CNBC Indonesia, CNN Indonesia, BeritaSatu, Garuda TV, Nusantara TV, DAAI TV.
- Channel bisa mati kapan saja setelah snapshot ini. Kalau banyak yang mati, tinggal ulangi
  proses verifikasi (lihat bawah).

## Regenerate

```bash
curl -s https://iptv-org.github.io/iptv/index.m3u | tr -d '\r' > index.m3u
# verifikasi + split pakai skrip di scripts/
python3 scripts/verify.py urls.txt
python3 scripts/build.py
```

Sumber data channel: [iptv-org/database](https://github.com/iptv-org/database) ·
EPG: [iptv-org/epg](https://github.com/iptv-org/epg)
