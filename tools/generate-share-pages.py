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
<link rel="canonical" href="{url_share}">
<meta property="og:image" content="{gambar}">
<meta property="article:published_time" content="{tanggal}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{judul}">
<meta name="twitter:description" content="{ringkasan}">
<meta name="twitter:image" content="{gambar}">
<script type="application/ld+json">
{jsonld}
</script>
<meta http-equiv="refresh" content="0; url=/#baca/{id_url}">
<script>location.replace("/#baca/{id_url}");</script>
</head>
<body>
<p>Membuka berita di Potret Sekitar…</p>
<p><a href="/#baca/{id_url}">{judul}</a></p>
{terkait}
</body>
</html>
"""


def potong(teks, batas=200):
    teks = " ".join((teks or "").split())
    if len(teks) <= batas:
        return teks
    return teks[: batas - 1].rstrip() + "…"


def tanggal_iso(b):
    """Tanggal artikel sebagai ISO 8601 lengkap dengan zona waktu."""
    t = str(b.get("tanggal", "")).strip()
    if len(t) == 10:
        t += "T00:00:00+07:00"
    return t


def buat_jsonld(b, url_share, gambar):
    """Structured data NewsArticle untuk halaman baca statis."""
    ringkasan = potong(b.get("ringkasan") or b.get("judul", ""))
    ld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "mainEntityOfPage": {"@type": "WebPage", "@id": url_share},
        "headline": b.get("judul", ""),
        "description": ringkasan,
        "image": [gambar],
        "datePublished": tanggal_iso(b),
        "dateModified": tanggal_iso(b),
        "author": {
            "@type": "Organization",
            "name": "Potret Sekitar",
            "url": BASE + "/",
        },
        "publisher": {
            "@type": "Organization",
            "name": "Potret Sekitar",
            "url": BASE + "/",
            "logo": {"@type": "ImageObject", "url": LOGO},
        },
        "inLanguage": "id-ID",
    }
    return json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/")


def buat_terkait(b, terbaru, maks=8):
    """Blok tautan crawlable: beranda + artikel terbaru lain."""
    lain = [a for a in terbaru if a["id"] != b["id"]][:maks]
    if not lain:
        return '<nav><p><a href="/">Beranda Potret Sekitar</a></p></nav>'
    item = "\n".join(
        '<li><a href="/baca/{}/">{}</a></li>'.format(
            a["id"], html.escape(a.get("judul", ""), quote=True)
        )
        for a in lain
    )
    return (
        "<nav>\n"
        '<p><a href="/">Beranda Potret Sekitar</a></p>\n'
        "<h2>Berita Terbaru Lainnya</h2>\n"
        "<ul>\n" + item + "\n</ul>\n</nav>"
    )


def main():
    with open(os.path.join(ROOT, "berita.json"), encoding="utf-8") as f:
        data = json.load(f)
    artikel = [b for b in data.get("berita", []) if b.get("terbit")]
    terbaru = sorted(
        artikel, key=lambda a: str(a.get("tanggal", "")), reverse=True
    )
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
        url_share = BASE + "/baca/" + bid + "/"
        halaman = TEMPLATE.format(
            judul=html.escape(b.get("judul", ""), quote=True),
            ringkasan=html.escape(
                potong(b.get("ringkasan") or b.get("judul", "")), quote=True
            ),
            url_share=url_share,
            gambar=html.escape(gambar, quote=True),
            tanggal=html.escape(tanggal_iso(b), quote=True),
            jsonld=buat_jsonld(b, url_share, gambar),
            terkait=buat_terkait(b, terbaru),
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




def buat_sitemap():
    """Tulis sitemap.xml: beranda + semua halaman baca artikel terbit."""
    import json as _json
    from xml.sax.saxutils import escape as _esc
    data = _json.load(open(os.path.join(ROOT, "berita.json"), encoding="utf-8"))
    upd = str(data.get("terakhirUpdate", ""))[:10]
    baris = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             f'  <url><loc>https://potretsekitar.my.id/</loc><lastmod>{upd}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>']
    arts = [a for a in data.get("berita", []) if a.get("terbit")]
    arts.sort(key=lambda a: a.get("tanggal", ""), reverse=True)
    for a in arts:
        tgl = str(a.get("tanggal", upd))[:10]
        baris.append(f'  <url><loc>https://potretsekitar.my.id/baca/{_esc(a["id"])}/</loc><lastmod>{tgl}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>')
    baris.append('</urlset>')
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(baris) + "\n")
    print(f"Sitemap ditulis: {1 + len(arts)} URL.")

def buat_news_sitemap():
    """Tulis news-sitemap.xml: artikel bertanggal <=48 jam terakhir.

    Format Google News sitemap: tiap URL membawa blok <news:news>
    (nama publikasi, bahasa, tanggal terbit ISO 8601, judul).
    """
    from datetime import datetime, timedelta, timezone
    from xml.sax.saxutils import escape as _esc

    tz = timezone(timedelta(hours=7))
    now = datetime.now(tz)
    batas = now - timedelta(hours=48)
    data = json.load(open(os.path.join(ROOT, "berita.json"), encoding="utf-8"))
    kandidat = []
    for a in data.get("berita", []):
        if not a.get("terbit"):
            continue
        try:
            tgl = datetime.fromisoformat(str(a.get("tanggal", "")))
        except ValueError:
            continue
        if tgl.tzinfo is None:
            tgl = tgl.replace(tzinfo=tz)
        if batas <= tgl <= now + timedelta(hours=1):
            kandidat.append((tgl, a))
    kandidat.sort(key=lambda x: x[0], reverse=True)
    baris = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">',
    ]
    for tgl, a in kandidat:
        baris.append("  <url>")
        baris.append(
            f'    <loc>https://potretsekitar.my.id/baca/{_esc(a["id"])}/</loc>'
        )
        baris.append("    <news:news>")
        baris.append("      <news:publication>")
        baris.append("        <news:name>Potret Sekitar</news:name>")
        baris.append("        <news:language>id</news:language>")
        baris.append("      </news:publication>")
        baris.append(
            f"      <news:publication_date>{tgl.isoformat()}</news:publication_date>"
        )
        baris.append(f'      <news:title>{_esc(a.get("judul", ""))}</news:title>')
        baris.append("    </news:news>")
        baris.append("  </url>")
    baris.append("</urlset>")
    with open(os.path.join(ROOT, "news-sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(baris) + "\n")
    print(f"News sitemap ditulis: {len(kandidat)} artikel (48 jam terakhir).")


if __name__ == "__main__":
    _kode = main()
    if _kode == 0:
        buat_sitemap()
        buat_news_sitemap()
    sys.exit(_kode)
