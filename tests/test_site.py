"""Sanity tests for the static site. Standard library only, so they run in any
Python 3 environment:  python -m unittest discover -s tests -v"""
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

SITE = Path(__file__).resolve().parent.parent / "site"
REQUIRED_SECTIONS = {"top", "work", "about", "experience", "contact"}


class PageScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs, self.h1_count = set(), [], 0
        self.title, self.description, self.lang = "", "", None
        self.imgs_without_alt = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "h1":
            self.h1_count += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta" and a.get("name") == "description":
            self.description = a.get("content", "")
        if tag == "img" and "alt" not in a:
            self.imgs_without_alt += 1
        for key in ("href", "src", "action"):
            if key in a:
                self.refs.append(a[key])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def scan(name):
    parser = PageScan()
    parser.feed((SITE / name).read_text(encoding="utf-8"))
    return parser


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.page = scan("index.html")

    def test_basic_metadata(self):
        self.assertEqual(self.page.lang, "en")
        self.assertTrue(self.page.title.strip())
        self.assertGreater(len(self.page.description), 40)

    def test_single_h1(self):
        self.assertEqual(self.page.h1_count, 1)

    def test_required_sections_exist(self):
        self.assertTrue(REQUIRED_SECTIONS <= self.page.ids, REQUIRED_SECTIONS - self.page.ids)

    def test_images_have_alt_text(self):
        self.assertEqual(self.page.imgs_without_alt, 0)

    def test_local_files_referenced_exist(self):
        for ref in self.page.refs:
            parsed = urlparse(ref)
            if parsed.scheme or ref.startswith(("#", "//", "data:")):
                continue
            target = SITE / parsed.path.lstrip("/")
            self.assertTrue(target.is_file(), f"index.html references missing file: {ref}")

    def test_in_page_anchors_resolve(self):
        for ref in self.page.refs:
            if ref.startswith("#") and len(ref) > 1:
                self.assertIn(ref[1:], self.page.ids, f"broken anchor {ref}")

    def test_external_links_are_https_or_mailto(self):
        for ref in self.page.refs:
            scheme = urlparse(ref).scheme
            self.assertIn(scheme, ("", "https", "mailto"), f"unexpected link scheme: {ref}")

    def test_404_page_exists_and_has_title(self):
        self.assertTrue(scan("404.html").title.strip())

    def test_static_assets_are_not_empty(self):
        for rel in ("css/style.css", "js/main.js", "js/theme.js", "assets/favicon.svg"):
            self.assertGreater((SITE / rel).stat().st_size, 50, rel)

    def test_version_file_is_valid_json(self):
        data = json.loads((SITE / "version.json").read_text())
        self.assertIn("version", data)


if __name__ == "__main__":
    unittest.main()
