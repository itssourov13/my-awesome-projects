#!/usr/bin/env python3
"""Validate the project catalog and static site before preview/deploy."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
WARNINGS: list[str] = []


def error(message: str) -> None:
    ERRORS.append(message)


def warn(message: str) -> None:
    WARNINGS.append(message)


def checked_local_file(value: str, label: str, owner: str) -> None:
    if not value:
        error(f"{owner}: {label} is empty")
        return
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or value.startswith("/"):
        error(f"{owner}: {label} must be a local relative path, got {value!r}")
        return
    if ".." in Path(value).parts:
        error(f"{owner}: {label} may not traverse outside the repository: {value!r}")
        return
    if not (ROOT / value).is_file():
        error(f"{owner}: missing {label}: {value}")


def validate_https_url(url: str, label: str, owner: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        error(f"{owner}: {label} must be a full HTTPS URL")


def main() -> int:
    catalog_path = ROOT / "projects.json"
    if not catalog_path.is_file():
        print("ERROR: projects.json is missing")
        return 1

    try:
        projects = json.loads(catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: projects.json is invalid at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return 1

    if not isinstance(projects, list):
        error("projects.json must contain an array")
        projects = []

    ids: set[str] = set()
    public_count = 0
    hidden_count = 0
    live_count = 0
    category_names: set[str] = set()
    gallery_item_count = 0

    for idx, project in enumerate(projects, start=1):
        if not isinstance(project, dict):
            error(f"entry {idx}: must be an object")
            continue
        owner = project.get("id", f"entry {idx}")
        for key in ("id", "title", "category", "description", "sourceAccess", "cover", "gallery"):
            if key not in project:
                error(f"{owner}: missing required field {key!r}")
        project_id = project.get("id")
        if not isinstance(project_id, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", project_id):
            error(f"{owner}: id must contain only letters, digits, dot, underscore, or hyphen")
        elif project_id in ids:
            error(f"{owner}: duplicate project id")
        else:
            ids.add(project_id)

        category = project.get("category")
        if isinstance(category, str) and category:
            category_names.add(category)
        else:
            error(f"{owner}: category must be a non-empty string")

        access = project.get("sourceAccess")
        source_url = project.get("sourceUrl", "")
        if access == "public":
            public_count += 1
            if not source_url:
                error(f"{owner}: public source requires sourceUrl")
            else:
                validate_https_url(source_url, "sourceUrl", owner)
                parsed = urlparse(source_url)
                if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
                    error(f"{owner}: sourceUrl for a public repository must be on github.com")
        elif access == "hidden":
            hidden_count += 1
            if source_url:
                error(f"{owner}: hidden source must keep sourceUrl empty")
            if project.get("githubRepo"):
                error(f"{owner}: hidden-source entry must not expose an internal repository identifier")
            for field in ("description", "story", "demoNote", "eyebrow", "title"):
                if "github.com/" in str(project.get(field, "")).lower():
                    error(f"{owner}: hidden-source entry contains a GitHub URL in {field}")
        else:
            error(f"{owner}: sourceAccess must be 'public' or 'hidden'")

        live_url = project.get("liveUrl", "")
        if live_url:
            validate_https_url(live_url, "liveUrl", owner)
            live_count += 1

        if "live preview" in str(project.get("status", "")).lower() and not live_url:
            warn(f"{owner}: status says live preview but liveUrl is empty")

        checked_local_file(project.get("cover", ""), "cover", owner)
        gallery = project.get("gallery")
        if not isinstance(gallery, list) or not gallery:
            error(f"{owner}: gallery must be a non-empty array")
        else:
            for gallery_index, item in enumerate(gallery, start=1):
                gallery_item_count += 1
                if not isinstance(item, dict):
                    error(f"{owner}: gallery item {gallery_index} must be an object")
                    continue
                checked_local_file(item.get("src", ""), f"gallery item {gallery_index}", owner)
                alt = item.get("alt", "")
                if not isinstance(alt, str) or len(alt.strip()) < 6:
                    error(f"{owner}: gallery item {gallery_index} needs meaningful alt text")

        for url_key in ("sourceUrl", "liveUrl"):
            url_value = project.get(url_key, "")
            if url_value and any(char in url_value for char in "\r\n\t"):
                error(f"{owner}: {url_key} contains whitespace/control characters")

    required_files = (
        "index.html", "styles.css", "app.js", "README.md",
        "docs/PRIVATE_PROJECTS.md", "docs/ASSET_GUIDELINES.md",
        "docs/PROJECT_CATALOG.md", "REPORT.md",
        "scripts/generate_readme.py", "scripts/sync_public_projects.py",
        ".github/workflows/pages.yml", ".github/workflows/validate.yml",
    )
    for needed in required_files:
        if not (ROOT / needed).is_file():
            error(f"Required site file missing: {needed}")

    html_path = ROOT / "index.html"
    if html_path.is_file():
        html_text = html_path.read_text(encoding="utf-8")
        for ref in ('href="styles.css"', 'src="app.js"', 'href="assets/brand/favicon.svg"', 'content="assets/brand/og-cover.svg"'):
            if ref not in html_text:
                error(f"index.html does not contain expected reference {ref}")
        if re.search(r"https?://fonts\.googleapis\.com|https?://fonts\.gstatic\.com", html_text, re.I):
            warn("index.html references a remote font host; consider keeping the site self-contained")

    js_path = ROOT / "app.js"
    if js_path.is_file():
        js = js_path.read_text(encoding="utf-8")
        if 'fetch("projects.json"' not in js:
            error("app.js is not loading the local projects.json catalog")
        if "localStorage" not in js:
            warn("Theme preference is not persisted")
        if 'sourceAccess === "public"' not in js:
            error("app.js does not enforce public-source-only source buttons")
        if "project.gallery || project.screenshots" not in js:
            error("app.js does not use the visual gallery catalog")

    print("Project catalog validation")
    print(f"  Entries: {len(projects)}")
    print(f"  Categories: {len(category_names)}")
    print(f"  Public source entries: {public_count}")
    print(f"  Hidden source entries: {hidden_count}")
    print(f"  HTTPS preview URLs: {live_count}")
    print(f"  Local gallery visuals: {gallery_item_count}")
    for message in WARNINGS:
        print(f"WARNING: {message}")
    for message in ERRORS:
        print(f"ERROR: {message}")
    if ERRORS:
        print(f"FAILED: {len(ERRORS)} error(s), {len(WARNINGS)} warning(s).")
        return 1
    print(f"PASS: {len(WARNINGS)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
