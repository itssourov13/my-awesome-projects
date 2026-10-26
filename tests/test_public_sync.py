from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_readme
import sync_public_projects as sync


def repo(name: str, *, description: str = "A public test repository", pushed_at: str = "2026-10-24T12:00:00Z", language: str = "Python", private: bool = False) -> dict:
    return {
        "name": name,
        "full_name": f"itssourov13/{name}",
        "owner": {"login": "itssourov13"},
        "private": private,
        "visibility": "private" if private else "public",
        "html_url": f"https://github.com/itssourov13/{name}",
        "description": description,
        "pushed_at": pushed_at,
        "language": language,
        "topics": [],
        "archived": False,
    }


class FakeResponse:
    status = 200

    def __init__(self, payload: list[dict]):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class PublicSyncTests(unittest.TestCase):
    def test_inventory_excludes_private_repository_records(self):
        payload = [
            repo("public-tool"),
            repo("private-tool", private=True),
        ]
        with patch.object(sync, "urlopen", return_value=FakeResponse(payload)):
            result = sync.fetch_public_repositories()
        self.assertEqual([entry["name"] for entry in result], ["public-tool"])

    def test_catalog_reconciliation_rechecks_visibility_before_adding(self):
        # Defense in depth: even an accidentally unfiltered private record passed
        # directly to sync_catalog must not create a public source link or entry.
        projects, stats = sync.sync_catalog([], [repo("private-input", private=True)])
        self.assertEqual(projects, [])
        self.assertEqual(stats["new_public_entries"], 0)
        self.assertEqual(stats["public_repositories_verified"], 0)

    def test_new_public_repository_is_added_without_guessing_a_live_url(self):
        projects, stats = sync.sync_catalog([], [repo("sample-tool")])
        self.assertEqual(stats["new_public_entries"], 1)
        entry = projects[0]
        self.assertEqual(entry["sourceAccess"], "public")
        self.assertEqual(entry["sourceUrl"], "https://github.com/itssourov13/sample-tool")
        self.assertEqual(entry["liveUrl"], "")
        self.assertEqual(entry["syncMode"], "github")
        self.assertEqual(entry["githubRepo"], "sample-tool")

    def test_curated_public_entry_updates_push_date_but_keeps_copy(self):
        entry = {
            "id": "my-tool",
            "title": "Curated Tool Name",
            "description": "Carefully reviewed public-facing description.",
            "category": "Cybersecurity",
            "sourceAccess": "public",
            "sourceUrl": "https://github.com/itssourov13/my-tool",
            "liveUrl": "",
            "updated": "2026-08-01",
            "cover": "assets/projects/my-tool/cover.svg",
            "gallery": [{"src": "assets/projects/my-tool/gallery/01-feature.svg", "alt": "Curated feature panel"}],
        }
        projects, stats = sync.sync_catalog([entry], [repo("my-tool", description="Short GitHub tagline")])
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["updated"], "2026-10-24")
        self.assertEqual(projects[0]["title"], "Curated Tool Name")
        self.assertEqual(projects[0]["description"], "Carefully reviewed public-facing description.")
        self.assertEqual(projects[0]["cover"], "assets/projects/my-tool/cover.svg")
        self.assertEqual(stats["updated_existing_entries"], 1)

    def test_repository_no_longer_public_loses_source_link(self):
        entry = {
            "id": "now-private",
            "title": "Now Private",
            "sourceAccess": "public",
            "sourceUrl": "https://github.com/itssourov13/now-private",
            "githubRepo": "now-private",
            "liveUrl": "https://demo.example.com/",
            "updated": "2026-10-01",
        }
        projects, stats = sync.sync_catalog([entry], [])
        self.assertEqual(projects[0]["sourceAccess"], "hidden")
        self.assertEqual(projects[0]["sourceUrl"], "")
        self.assertNotIn("githubRepo", projects[0])
        self.assertEqual(projects[0]["liveUrl"], "https://demo.example.com/")
        self.assertEqual(stats["source_links_hidden_for_safety"], 1)

    def test_hidden_curated_project_is_not_duplicated_or_exposed(self):
        hidden = {
            "id": "scholarhub",
            "title": "ScholarHub",
            "sourceAccess": "hidden",
            "sourceUrl": "",
            "liveUrl": "https://scholarhub-itssourov13.vercel.app/",
        }
        projects, stats = sync.sync_catalog([hidden], [repo("scholar-hub")])
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["sourceAccess"], "hidden")
        self.assertEqual(projects[0]["sourceUrl"], "")
        self.assertEqual(projects[0]["liveUrl"], "https://scholarhub-itssourov13.vercel.app/")
        self.assertEqual(stats["new_public_entries"], 0)

    def test_generated_public_entry_follows_github_description(self):
        first = repo("generated-tool", description="First public summary")
        projects, _ = sync.sync_catalog([], [first])
        second = repo("generated-tool", description="Updated public summary", pushed_at="2026-10-25T08:00:00Z", language="TypeScript")
        projects, _ = sync.sync_catalog(projects, [second])
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["description"], "Updated public summary")
        self.assertEqual(projects[0]["stack"], ["TypeScript"])
        self.assertEqual(projects[0]["updated"], "2026-10-25")

    def test_readme_never_renders_a_hidden_source_url(self):
        projects = [
            {
                "id": "private-app",
                "title": "Private App",
                "category": "Web Apps",
                "description": "Approved public description",
                "stack": ["TypeScript"],
                "sourceAccess": "hidden",
                "sourceUrl": "",
                "liveUrl": "https://demo.example.com/",
                "status": "Live preview listed",
                "cover": "assets/brand/og-cover.svg",
                "gallery": [],
            }
        ]
        content = generate_readme.build_readme(projects)
        self.assertIn("https://demo.example.com/", content)
        self.assertIn("Source hidden", content)
        self.assertNotIn("github.com/private-app", content)
        self.assertNotIn("githubRepo", content)


if __name__ == "__main__":
    unittest.main()
