from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


def test_homepage_has_search_and_accessibility_basics():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    assert soup.html.get("lang") == "vi"
    assert soup.title and "Xoso88" in soup.title.get_text()
    assert soup.find("meta", attrs={"name": "description"})
    assert soup.find("meta", attrs={"name": "robots"})
    canonical = soup.find("link", attrs={"rel": "canonical"})
    assert canonical and canonical.get("href", "").startswith("https://")
    assert soup.find(id="date")
    assert soup.find(id="recentDates")
    assert soup.find(id="results")
    assert len(soup.select("[data-region]")) == 3
    assert soup.select_one('[aria-live="polite"]')
    assert soup.select_one(".result-table") is None  # rendered from verified API data
    slots = {node.get("data-ad-slot") for node in soup.select("[data-ad-slot]")}
    expected_slots = {
        "top-970x90",
        "left-top-160x600",
        "left-bottom-160x600",
        "content-top-728x90",
        "mobile-320x100",
        "content-bottom-728x90",
        "mobile-bottom-320x100",
        "right-top-300x250",
        "right-middle-300x600",
        "right-bottom-300x250",
        "footer-970x90",
    }
    assert expected_slots <= slots
    assert len(slots) >= 11
    assert "renderResults(draws)" in html


def test_structured_data_is_valid_json():
    soup = BeautifulSoup((WEB / "index.html").read_text(encoding="utf-8"), "html.parser")
    script = soup.find("script", attrs={"type": "application/ld+json"})
    assert script is not None
    payload = json.loads(script.string)
    assert payload["@type"] == "WebSite"
    assert payload["name"] == "Xoso88"


def test_robots_and_sitemap_reference_public_site():
    robots = (WEB / "robots.txt").read_text(encoding="utf-8")
    assert "Allow: /" in robots
    assert "https://duykhanhrungnhum-debug.github.io/X-s-88/sitemap.xml" in robots

    tree = ET.parse(WEB / "sitemap.xml")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    loc = tree.find(".//sm:loc", ns)
    assert loc is not None
    assert loc.text == "https://duykhanhrungnhum-debug.github.io/X-s-88/"


def test_inline_frontend_javascript_syntax():
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available")

    soup = BeautifulSoup((WEB / "index.html").read_text(encoding="utf-8"), "html.parser")
    scripts = [
        s.get_text()
        for s in soup.find_all("script")
        if s.get("type") != "application/ld+json" and not s.get("src")
    ]
    assert scripts

    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as f:
        f.write("\n".join(scripts))
        path = f.name
    result = subprocess.run([node, "--check", path], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
