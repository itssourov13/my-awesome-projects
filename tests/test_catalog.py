from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))


class CatalogTests(unittest.TestCase):
    def test_project_ids_are_unique(self):
        ids = [project["id"] for project in PROJECTS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_cover_exists(self):
        for project in PROJECTS:
            with self.subTest(project=project["id"]):
                self.assertTrue((ROOT / project["cover"]).is_file())

    def test_hidden_source_never_has_a_source_url(self):
        hidden = [p for p in PROJECTS if p["sourceAccess"] == "hidden"]
        self.assertGreaterEqual(len(hidden), 1)
        for project in hidden:
            with self.subTest(project=project["id"]):
                self.assertEqual(project.get("sourceUrl", ""), "")

    def test_source_links_are_only_public_github_urls(self):
        for project in PROJECTS:
            with self.subTest(project=project["id"]):
                if project["sourceAccess"] == "public":
                    parsed = urlparse(project["sourceUrl"])
                    self.assertEqual(parsed.scheme, "https")
                    self.assertIn(parsed.netloc.lower(), {"github.com", "www.github.com"})

    def test_live_links_are_https(self):
        for project in PROJECTS:
            with self.subTest(project=project["id"]):
                live_url = project.get("liveUrl", "")
                if live_url:
                    parsed = urlparse(live_url)
                    self.assertEqual(parsed.scheme, "https")
                    self.assertTrue(parsed.netloc)

    def test_visual_gallery_assets_exist_and_have_alt_text(self):
        for project in PROJECTS:
            gallery = project.get("gallery", project.get("screenshots", []))
            self.assertGreaterEqual(len(gallery), 1, project["id"])
            for index, item in enumerate(gallery):
                with self.subTest(project=project["id"], image=index):
                    self.assertTrue((ROOT / item["src"]).is_file())
                    self.assertGreaterEqual(len(item.get("alt", "").strip()), 6)

    def test_private_source_does_not_publish_a_github_url_in_text(self):
        for project in PROJECTS:
            if project["sourceAccess"] != "hidden":
                continue
            with self.subTest(project=project["id"]):
                for key in ("description", "story", "demoNote"):
                    self.assertNotIn("github.com/", str(project.get(key, "")).lower())

    def test_private_vulnerable_lab_has_no_public_preview_link(self):
        project = next(item for item in PROJECTS if item["id"] == "personal-website-pentest")
        self.assertEqual(project.get("liveUrl", ""), "")
        self.assertIn("deliberately vulnerable", project["description"].lower())

    def test_catalog_is_large_enough_for_an_index(self):
        self.assertGreaterEqual(len(PROJECTS), 25)


if __name__ == "__main__":
    unittest.main()
