#!/usr/bin/env python3
"""Generate the repository README as the primary visual project showcase."""
from __future__ import annotations

import argparse
import html
import json
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "projects.json"
README = ROOT / "README.md"
OWNER = "itssourov13"
SITE_URL = "https://itssourov13.github.io/my-awesome-projects/"
PROFILE_URL = f"https://github.com/{OWNER}"
CATEGORY_ORDER = [
    "Cybersecurity", "AI & Developer Tools", "Web Apps", "Creative & 3D",
    "Mobile Apps", "Utilities", "Writing & Publishing", "Open Source",
]
FEATURED_LIMIT = 6
BEGIN = "<!-- GENERATED SHOWCASE:BEGIN -->"
END = "<!-- GENERATED SHOWCASE:END -->"


def h(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def safe_https(value: object) -> str:
    if not isinstance(value, str):
        return ""
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or any(c in value for c in "\r\n\t"):
        return ""
    return value


def safe_source(project: dict) -> str:
    if project.get("sourceAccess") != "public":
        return ""
    url = safe_https(project.get("sourceUrl"))
    parsed = urlparse(url)
    return url if parsed.netloc.casefold() in {"github.com", "www.github.com"} else ""


def safe_asset(value: object) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        return ""
    path = Path(value)
    if ".." in path.parts or path.is_absolute():
        return ""
    full = ROOT / path
    try:
        full.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return ""
    return value if full.is_file() else ""


def external_actions(project: dict) -> str:
    links: list[str] = []
    live = safe_https(project.get("liveUrl"))
    source = safe_source(project)
    if live:
        links.append(f'<a href="{h(live)}">Live preview ↗</a>')
    if source:
        links.append(f'<a href="{h(source)}">Public source ↗</a>')
    if project.get("sourceAccess") == "hidden":
        links.append('<span><em>Source hidden</em></span>')
    if not links:
        links.append('<span><em>No public link listed</em></span>')
    return " &nbsp;·&nbsp; ".join(links)


def project_card(project: dict) -> str:
    title = h(project.get("title", "Untitled project"))
    title_target = safe_https(project.get("liveUrl")) or safe_source(project)
    title_markup = f'<a href="{h(title_target)}">{title}</a>' if title_target else title
    cover = safe_asset(project.get("cover"))
    image = (
        f'<img src="{h(cover)}" alt="{title} — original project cover artwork" width="100%">'
        if cover else f'<p><strong>{title}</strong></p>'
    )
    category = h(project.get("category", "Uncategorized"))
    status = h(project.get("status", "Status not listed"))
    description = h(project.get("description", "A project in the archive."))
    stack = project.get("stack") if isinstance(project.get("stack"), list) else []
    stack_text = h(" · ".join(str(item) for item in stack[:5])) or "Not specified"
    return (
        '<td width="50%" valign="top" style="padding:14px;">'
        f"{image}<h3>{title_markup}</h3>"
        f"<p><strong>{category}</strong> &nbsp;·&nbsp; <code>{status}</code></p>"
        f"<p>{description}</p>"
        f"<p><sub><strong>Stack:</strong> {stack_text}</sub></p>"
        f"<p>{external_actions(project)}</p></td>"
    )


def card_table(projects: list[dict]) -> str:
    if not projects:
        return "_More projects will appear here as they are added._"
    rows: list[str] = []
    for index in range(0, len(projects), 2):
        pair = [project_card(p) for p in projects[index:index + 2]]
        if len(pair) == 1:
            pair.append('<td width="50%" valign="top"></td>')
        rows.append("<tr>" + "".join(pair) + "</tr>")
    return '<table width="100%">\n' + "\n".join(rows) + "\n</table>"


def build_readme(projects: list[dict]) -> str:
    if any(not isinstance(p, dict) for p in projects):
        raise ValueError("projects.json must contain only project objects.")
    ids = [p.get("id") for p in projects]
    if len(ids) != len(set(ids)):
        raise ValueError("Project IDs must be unique before README generation.")

    categories: dict[str, list[dict]] = defaultdict(list)
    for project in projects:
        categories[str(project.get("category") or "Uncategorized")].append(project)
    category_count = len(categories)
    public_count = sum(p.get("sourceAccess") == "public" and bool(safe_source(p)) for p in projects)
    hidden_count = sum(p.get("sourceAccess") == "hidden" for p in projects)
    live_count = sum(bool(safe_https(p.get("liveUrl"))) for p in projects)
    updated = max((str(p.get("updated") or "") for p in projects), default="") or "Not listed"

    featured = sorted(
        (p for p in projects if p.get("featured")),
        key=lambda p: (str(p.get("updated") or ""), str(p.get("title") or "").casefold()),
        reverse=True,
    )[:FEATURED_LIMIT]
    featured_ids = {p["id"] for p in featured}

    lines = [
        BEGIN,
        '<div align="center">',
        '<img src="assets/brand/og-cover.svg" alt="My Awesome Projects — built to solve, made to explore" width="100%">',
        "",
        "<h1>My Awesome Projects</h1>",
        "<p><strong>A visual archive of software, security tooling, product experiments and creative computing.</strong></p>",
        f'<p><a href="{h(SITE_URL)}">Open the interactive showcase ↗</a> &nbsp;·&nbsp; <a href="{h(PROFILE_URL)}">GitHub profile ↗</a></p>',
        "</div>",
        "",
        f"> **{len(projects)} projects** &nbsp;·&nbsp; **{category_count} disciplines** &nbsp;·&nbsp; **{public_count} public sources** &nbsp;·&nbsp; **{live_count} live previews**",
        "",
        "This README is the **main project showcase**. The companion website provides search, category filters, sorting, detail views and a visual gallery.",
        "",
        "## How to explore",
        "",
        "- **Public projects** link to their public source repository when that source is verified.",
        "- **Private or unpublished projects** can show approved descriptions and graphics without a source link.",
        "- **Live previews are separate from source visibility.** A preview is listed only when its HTTPS URL is approved for public visitors.",
        "- Covers and feature panels are portfolio artwork, not claims that every feature is production-ready or real UI screenshots.",
        "",
    ]
    if featured:
        lines.extend(["## Selected work", "", card_table(featured), ""])
    lines.extend(["## Complete project archive", ""])
    lines.append(
        f"<p><sub>Public-source entries: {public_count} · Source-hidden entries: {hidden_count} · "
        f"Latest recorded project update in the catalog: {h(updated)}.</sub></p>"
    )
    for category in CATEGORY_ORDER + sorted(c for c in categories if c not in CATEGORY_ORDER):
        entries = sorted(
            (p for p in categories[category] if p.get("id") not in featured_ids),
            key=lambda p: str(p.get("title") or "").casefold(),
        )
        if entries:
            lines.extend([f"### {category}", "", card_table(entries), ""])
    lines.extend([
        "## Source privacy & live preview policy",
        "",
        "Private repository code is not mirrored here. For a source-hidden entry, the catalog keeps <code>sourceUrl</code> empty; no source button or source link is generated. Its public live URL may still be displayed independently after anonymous access and deployment safety are verified.",
        "",
        "For deliberately vulnerable labs, internal dashboards, or systems containing real data, do not publish a preview until isolation, synthetic data, access controls and exposed routes have been reviewed.",
        "",
        f'<p align="center"><a href="{h(SITE_URL)}"><strong>Explore the full interactive showcase ↗</strong></a></p>',
        "",
        "<sub>Catalog source: projects.json · README generated by scripts/generate_readme.py · Public repository sync never imports private repository metadata.</sub>",
        '<p align="center"><sub><a href="docs/PRIVATE_PROJECTS.md">Private-project policy</a> · <a href="docs/ASSET_GUIDELINES.md">Asset guidelines</a> · <a href="docs/PROJECT_CATALOG.md">Catalog notes</a></sub></p>',
        END,
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when README.md differs from the generated showcase")
    args = parser.parse_args()
    try:
        projects = json.loads(CATALOG.read_text(encoding="utf-8"))
        if not isinstance(projects, list):
            raise ValueError("projects.json must contain an array.")
        generated = build_readme(projects)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"README generation failed: {exc}", file=sys.stderr)
        return 1
    if args.check:
        current = README.read_text(encoding="utf-8") if README.exists() else ""
        if current != generated:
            print("README.md is stale. Run: python3 scripts/generate_readme.py", file=sys.stderr)
            return 1
        print(f"README check passed: {len(projects)} projects, {len(set(p.get('category') for p in projects))} categories.")
        return 0
    README.write_text(generated, encoding="utf-8")
    print(f"Generated README.md visual showcase for {len(projects)} projects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
