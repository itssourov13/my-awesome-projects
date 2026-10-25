from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
PROJECTS = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
PROFILE = "https://github.com/itssourov13"
REPO = PROFILE + "/my-awesome-projects"


def load_readme_generator():
    spec = importlib.util.spec_from_file_location("generate_readme", ROOT / "scripts" / "generate_readme.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SiteContractTests(unittest.TestCase):
    def test_every_element_id_used_by_app_js_exists_in_html(self):
        ids = set(re.findall(r'\$\("#([A-Za-z0-9_-]+)"', JS))
        self.assertGreater(len(ids), 10)
        for element_id in sorted(ids):
            with self.subTest(id=element_id):
                # Static ids live in index.html; dialog ids are created by app.js templates.
                self.assertTrue(f'id="{element_id}"' in HTML or f'id="{element_id}"' in JS, f"missing id {element_id}")

    def test_footer_has_navigation_categories_profile_and_copyright(self):
        footer = HTML[HTML.index('<footer class="site-footer"'):HTML.index("</footer>")]
        for needle in (
            'href="#featured"', 'href="#project-index"', 'href="#about-index"',
            'id="footer-categories"', 'href="https://github.com/itssourov13"', "©", 'id="back-to-top"',
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, footer)

    def test_nav_and_footer_anchor_targets_exist(self):
        for anchor in ("featured", "project-index", "about-index", "main", "top"):
            with self.subTest(anchor=anchor):
                self.assertIn(f'id="{anchor}"', HTML)

    def test_static_github_links_are_only_profile_and_this_repository(self):
        links = re.findall(r'href="(https://github\.com[^"]*)"', HTML)
        self.assertTrue(links)
        for link in links:
            with self.subTest(link=link):
                self.assertTrue(
                    link in (PROFILE, REPO)
                    or link.startswith((REPO + "#", REPO + "/blob/main/docs/")),
                    link,
                )

    def test_hidden_source_identifiers_never_appear_in_site_files(self):
        for project in PROJECTS:
            if project.get("sourceAccess") != "hidden":
                continue
            for key in ("githubRepo", "sourceUrl"):
                value = str(project.get(key) or "")
                if not value:
                    continue
                for name, text in (("index.html", HTML), ("app.js", JS), ("styles.css", CSS)):
                    with self.subTest(project=project["id"], key=key, file=name):
                        self.assertNotIn(value, text)

    def test_app_js_gates_source_links_on_public_github_sources(self):
        self.assertIn('sourceAccess === "public"', JS)
        self.assertIn("isGithubUrl", JS)
        self.assertNotIn("githubRepo", JS)

    def test_category_order_and_featured_limit_match_readme_generator(self):
        readme = load_readme_generator()
        block = re.search(r"const CATEGORY_ORDER = \[(.*?)\];", JS, re.S).group(1)
        js_order = re.findall(r'"([^"]+)"', block)
        self.assertEqual(js_order, readme.CATEGORY_ORDER)
        limit = int(re.search(r"const FEATURED_LIMIT = (\d+);", JS).group(1))
        self.assertEqual(limit, readme.FEATURED_LIMIT)

    def test_sort_options_in_html_match_app_js(self):
        html_values = re.findall(r'<option value="([^"]+)"', HTML)
        js_values = re.findall(r'"([a-z]+)"', re.search(r"const SORTS = \[(.*?)\];", JS, re.S).group(1))
        self.assertEqual(html_values, js_values)

    def test_filter_counts_exclude_the_chip_being_previewed(self):
        self.assertIn('matches(item, { ignoreCategory: true })', JS)
        self.assertIn('matches(item, { ignoreFlag: flag })', JS)
        self.assertIn('matches(item, { ignoreTech: key })', JS)
        self.assertIn('(active || FLAGS[flag].test(item))', JS)
        self.assertIn('(active || item.tech.has(key))', JS)
        self.assertIn('flag !== ignoreFlag', JS)
        self.assertIn('key !== ignoreTech', JS)
        self.assertIn('chip.disabled = count === 0 && !active', JS)
        self.assertIn('.filter-chip:disabled', CSS)

    def test_project_dialog_restores_focus_after_related_project_navigation(self):
        open_project = re.search(r"function openProject\(projectId\) \{(.*?)\n  \}", JS, re.S).group(1)
        self.assertIn('$(".dialog-close", els.dialog)', open_project)
        self.assertIn('closeButton.focus({ preventScroll: true })', open_project)

    def test_site_respects_reduced_motion_and_keeps_theme_tokens(self):
        self.assertIn("prefers-reduced-motion: reduce", CSS)
        self.assertIn(':root[data-theme="light"]', CSS)
        self.assertIn("awesome-projects-theme", JS)
        self.assertIn("awesome-projects-theme", HTML)


if __name__ == "__main__":
    unittest.main()
