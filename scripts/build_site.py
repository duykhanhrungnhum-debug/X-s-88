from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DIST = ROOT / "dist"
SITE_URL = "https://duykhanhrungnhum-debug.github.io/X-s-88/"
REGION_NAMES = {
    "north": "Miền Bắc",
    "central": "Miền Trung",
    "south": "Miền Nam",
}


def build() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)

    shutil.copytree(
        WEB,
        DIST,
        ignore=shutil.ignore_patterns("province-template.html"),
    )

    provinces = json.loads((WEB / "provinces.json").read_text(encoding="utf-8"))
    template = (WEB / "province-template.html").read_text(encoding="utf-8")

    seen_codes: set[str] = set()
    for province in provinces:
        code = province["code"].strip()
        name = province["name"].strip()
        region = province["region"].strip()
        if not code or code in seen_codes:
            raise ValueError(f"Duplicate or empty province code: {code!r}")
        if region not in REGION_NAMES:
            raise ValueError(f"Unsupported region {region!r} for {name}")
        seen_codes.add(code)

        canonical = f"{SITE_URL}tinh/{code}/"
        page = (
            template.replace("{{PROVINCE_NAME}}", html.escape(name))
            .replace("{{PROVINCE_NAME_JSON}}", json.dumps(name, ensure_ascii=False))
            .replace("{{PROVINCE_CODE}}", code)
            .replace("{{REGION}}", region)
            .replace("{{REGION_NAME}}", REGION_NAMES[region])
            .replace("{{CANONICAL_URL}}", canonical)
            .replace("{{SITE_URL}}", SITE_URL)
        )
        out = DIST / "tinh" / code / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")

    build_directory(provinces)
    build_sitemap(provinces)


def build_directory(provinces: list[dict[str, str]]) -> None:
    groups: dict[str, list[dict[str, str]]] = {key: [] for key in REGION_NAMES}
    for province in provinces:
        groups[province["region"]].append(province)

    blocks = []
    for region in ("south", "central", "north"):
        links = "".join(
            f'<a href="./{html.escape(p["code"])}/">{html.escape(p["name"])}</a>'
            for p in groups[region]
        )
        blocks.append(
            f'<section><h2>{REGION_NAMES[region]}</h2><div class="grid">{links}</div></section>'
        )

    page = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Danh sách tỉnh thành để tra cứu kết quả xổ số đã xác thực trên Xoso88.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{SITE_URL}tinh/">
<title>Tra cứu xổ số theo tỉnh — Xoso88</title>
<style>
:root{{font-family:Arial,Helvetica,sans-serif;color:#202733;--blue:#075baa;--line:#d9dee5}}
*{{box-sizing:border-box}}body{{margin:0;background:#f7f8fa}}header{{background:var(--blue);color:#fff}}header div,main{{max-width:980px;margin:auto;padding:14px}}.brand{{font-size:24px;font-weight:900;color:#fff;text-decoration:none}}h1{{font-size:23px}}section{{background:#fff;border:1px solid var(--line);padding:14px;margin:12px 0}}h2{{font-size:17px;color:#0b4f91;margin:0 0 10px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}}.grid a{{border:1px solid var(--line);border-radius:5px;padding:9px 10px;text-decoration:none;color:#075baa;font-weight:700}}.grid a:hover{{background:#eef5fc}}p{{color:#687483}}
</style>
</head>
<body>
<header><div><a class="brand" href="{SITE_URL}">Xoso88</a></div></header>
<main>
<h1>Tra cứu kết quả xổ số theo tỉnh</h1>
<p>Chọn tỉnh/thành để xem kỳ quay mới nhất và lịch sử kết quả đã xác thực.</p>
{''.join(blocks)}
</main>
</body>
</html>
"""
    out = DIST / "tinh" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")


def build_sitemap(provinces: list[dict[str, str]]) -> None:
    urls = [SITE_URL, f"{SITE_URL}tinh/"] + [
        f'{SITE_URL}tinh/{p["code"]}/' for p in provinces
    ]
    entries = "\n".join(
        f"  <url><loc>{html.escape(url)}</loc><changefreq>daily</changefreq></url>"
        for url in urls
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")


if __name__ == "__main__":
    build()
