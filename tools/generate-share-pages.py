#!/usr/bin/env python3
"""Generator halaman share statis per artikel Potret Sekitar.

Membuat baca/<id>/index.html untuk setiap artikel terbit di berita.json.
Halaman ini membawa OG/Twitter tags dengan foto artikel itu sendiri
(og:image = foto utama artikel) lalu langsung mengalihkan pengunjung
manusia ke aplikasi SPA di /#baca/<id>.

Kenapa perlu: rute artikel SPA berupa hash (#baca/<id>) tidak pernah
sampai ke server, jadi perayap WhatsApp/Facebook/Telegram hanya menerima
index.html dengan OG generik (logo situs). Halaman statis ini yang
dibagikan ke luar, sehingga pratinjau menampilkan foto beritanya.

Jalankan setiap selesai menambah/mengubah artikel, sebelum commit:
    python3 tools/generate-share-pages.py
"""
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://potretsekitar.my.id"
LOGO = BASE + "/logo-potret.png"

TEMPLATE = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{judul} — Potret Sekitar</title>
<meta name="description" content="{ringkasan}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Potret Sekitar">
<meta property="og:title" content="{judul}">
<meta property="og:description" content="{ringkasan}">
<meta property="og:url" content="{url_share}">
<meta property="og:image" content="{gambar}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{judul}">
<meta name="twitter:description" content="{ringkasan}">
<meta name="twitter:image" content="{gambar}">
<meta http-equiv="refresh" content="0; url=/#baca/{id_url}">
<script>location.replace("/#baca/{id_url}");</script>
</head>
<body>
<p>Membuka berita di Potret Sekitar…</p>
<p><a href="/#baca/{id_url}">{judul}</a></p>
</body>
</html>
"""


def potong(teks, batas=200):
    teks = " ".join((teks or "").split())
    if len(teks) <= batas:
        return teks
    return teks[: batas - 1].rstrip() + "…"


def main():
    with open(os.path.join(ROOT, "berita.json"), encoding="utf-8") as f:
        data = json.load(f)
    artikel = [b for b in data.get("berita", []) if b.get("terbit")]
    dibuat = 0
    fallback = []
    for b in artikel:
        bid = b["id"]
        gambar_rel = (b.get("gambar") or "").lstrip("/")
        if gambar_rel and os.path.isfile(os.path.join(ROOT, gambar_rel)):
            gambar = BASE + "/" + gambar_rel
        else:
            gambar = LOGO
            fallback.append(bid)
        halaman = TEMPLATE.format(
            judul=html.escape(b.get("judul", ""), quote=True),
            ringkasan=html.escape(
                potong(b.get("ringkasan") or b.get("judul", "")), quote=True
            ),
            url_share=BASE + "/baca/" + bid + "/",
            gambar=html.escape(gambar, quote=True),
            id_url=bid,
        )
        folder = os.path.join(ROOT, "baca", bid)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
            f.write(halaman)
        dibuat += 1
    print(f"Halaman share dibuat: {dibuat} dari {len(artikel)} artikel terbit.")
    if fallback:
        print("Fallback logo (gambar tidak valid): " + ", ".join(fallback))
    else:
        print("Semua artikel memakai foto beritanya sendiri; tidak ada fallback logo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
