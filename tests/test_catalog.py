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

    def test_scholarhub_has_preview_without_source_link(self):
        project = next(item for item in PROJECTS if item["id"] == "scholarhub")
        self.assertEqual(project["sourceAccess"], "hidden")
        self.assertEqual(project.get("sourceUrl", ""), "")
        self.assertEqual(project["liveUrl"], "https://scholarhub-test.vercel.app/")

    def test_scholarhub_cover_uses_owner_banner_and_a_new_asset_path(self):
        sources = json.loads((ROOT / "assets/artwork-sources.json").read_text(encoding="utf-8"))
        source = next(item for item in sources if item["id"] == "scholarhub")
        project = next(item for item in PROJECTS if item["id"] == "scholarhub")
        self.assertEqual(source["kind"], "user-provided-banner")
        self.assertEqual(source["imagePath"], "assets/projects/scholarhub/source/cover-original-edited.webp")
        self.assertEqual(source["coverOutput"], "assets/projects/scholarhub/scholarhub-banner.webp")
        self.assertEqual(project["cover"], source["coverOutput"])
        self.assertTrue((ROOT / source["imagePath"]).is_file())
        self.assertTrue((ROOT / "assets/projects/scholarhub/source/cover-original.webp").is_file())
        self.assertTrue((ROOT / project["cover"]).is_file())
        self.assertFalse((ROOT / "assets/projects/scholarhub/cover.webp").exists())

    def test_private_vulnerable_lab_has_no_public_preview_link(self):
        project = next(item for item in PROJECTS if item["id"] == "personal-website-pentest")
        self.assertEqual(project.get("liveUrl", ""), "")
        self.assertIn("deliberately vulnerable", project["description"].lower())

    def test_public_artwork_provenance_matches_catalog(self):
        source_path = ROOT / "assets/artwork-sources.json"
        self.assertTrue(source_path.is_file())
        sources = json.loads(source_path.read_text(encoding="utf-8"))
        source_ids = [item["id"] for item in sources]
        catalog_ids = [item["id"] for item in PROJECTS]
        self.assertEqual(len(source_ids), len(set(source_ids)))
        self.assertEqual(set(source_ids), set(catalog_ids))
        for item in sources:
            with self.subTest(project=item["id"]):
                self.assertIn(item.get("status"), {"downloaded", "screenshot", "edited", "failed"})
                if item.get("status") != "failed":
                    image_path = item.get("imagePath", "")
                    self.assertTrue(image_path)
                    self.assertTrue((ROOT / image_path).is_file())

    def test_image_backed_covers_and_feature_panels_are_local_webp(self):
        for project in PROJECTS:
            cover = project.get("cover", "")
            if cover.endswith(".webp"):
                with self.subTest(project=project["id"], asset="cover"):
                    path = ROOT / cover
                    self.assertTrue(path.is_file())
                    self.assertGreater(path.stat().st_size, 10_000)
            for item in project.get("gallery", []):
                src = item.get("src", "")
                if src.endswith(".webp"):
                    with self.subTest(project=project["id"], asset=src):
                        path = ROOT / src
                        self.assertTrue(path.is_file())
                        self.assertGreater(path.stat().st_size, 10_000)

    def test_catalog_is_large_enough_for_an_index(self):
        self.assertGreaterEqual(len(PROJECTS), 25)


if __name__ == "__main__":
    unittest.main()
