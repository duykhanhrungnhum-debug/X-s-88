from pathlib import Path
import xml.etree.ElementTree as ET

from scripts import build_site


def test_build_generates_all_province_pages_and_directory(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    monkeypatch.setattr(build_site, "DIST", dist)

    build_site.build()

    provinces = __import__("json").loads(
        (build_site.WEB / "provinces.json").read_text(encoding="utf-8")
    )
    generated = list((dist / "tinh").glob("*/index.html"))
    assert len(generated) == len(provinces)
    assert (dist / "tinh" / "index.html").exists()

    tay_ninh = (dist / "tinh" / "tay-ninh" / "index.html").read_text(encoding="utf-8")
    assert "KẾT QUẢ XỔ SỐ Tây Ninh" in tay_ninh
    assert "PROVINCE_CODE='tay-ninh'" in tay_ninh
    assert "https://duykhanhrungnhum-debug.github.io/X-s-88/tinh/tay-ninh/" in tay_ninh

    directory = (dist / "tinh" / "index.html").read_text(encoding="utf-8")
    assert "Tra cứu kết quả xổ số theo tỉnh" in directory
    assert "./tay-ninh/" in directory
    assert "./da-nang/" in directory


def test_generated_sitemap_contains_province_pages(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    monkeypatch.setattr(build_site, "DIST", dist)

    build_site.build()

    tree = ET.parse(dist / "sitemap.xml")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = {node.text for node in tree.findall(".//sm:loc", ns)}
    assert "https://duykhanhrungnhum-debug.github.io/X-s-88/" in urls
    assert "https://duykhanhrungnhum-debug.github.io/X-s-88/tinh/" in urls
    assert "https://duykhanhrungnhum-debug.github.io/X-s-88/tinh/tay-ninh/" in urls
    assert "https://duykhanhrungnhum-debug.github.io/X-s-88/tinh/da-nang/" in urls
