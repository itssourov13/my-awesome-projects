#!/usr/bin/env python3
"""Generate the repository README as the primary visual project showcase."""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
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
FEATURED_LIMIT = 7
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
        links.append(f'<a href="{h(live)}"><strong>Live preview ↗</strong></a>')
    if source:
        links.append(f'<a href="{h(source)}">Public source ↗</a>')
    if project.get("sourceAccess") == "hidden":
        links.append("<em>Source hidden</em>")
    if not links:
        links.append("<em>No public link listed</em>")
    return " &nbsp;·&nbsp; ".join(links)


def slug(text: str) -> str:
    """Mirror GitHub's heading-anchor rules so in-page links resolve."""
    cleaned = re.sub(r"[^\w\- ]", "", text.strip().lower())
    return cleaned.replace(" ", "-")


def plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def stack_chips(project: dict, limit: int = 5) -> str:
    stack = project.get("stack") if isinstance(project.get("stack"), list) else []
    chips = " ".join(f"<code>{h(item)}</code>" for item in stack[:limit] if str(item).strip())
    return chips or "<sub>Stack not specified</sub>"


def title_markup(project: dict) -> str:
    title = h(project.get("title", "Untitled project"))
    target = safe_https(project.get("liveUrl")) or safe_source(project)
    return f'<a href="{h(target)}">{title}</a>' if target else title


def cover_markup(project: dict, width: str) -> str:
    title = h(project.get("title", "Untitled project"))
    cover = safe_asset(project.get("cover"))
    if not cover:
        return f"<strong>{title}</strong>"
    image = f'<img src="{h(cover)}" alt="{title} — project cover artwork" width="{width}">'
    target = safe_https(project.get("liveUrl")) or safe_source(project)
    return f'<a href="{h(target)}">{image}</a>' if target else image


def eyebrow(project: dict) -> str:
    label = str(project.get("eyebrow") or project.get("category") or "Project").strip()
    return h(label.upper())


def status_line(project: dict) -> str:
    return f"<sub>{h(project.get('status') or 'Status not listed')}</sub>"


def lead_card(project: dict) -> str:
    """Full-width spotlight: artwork left, editorial copy right."""
    return (
        '<table width="100%">\n<tr>\n'
        f'<td width="58%" valign="middle">{cover_markup(project, "100%")}</td>\n'
        '<td width="42%" valign="middle">'
        f'<sub><strong>{eyebrow(project)}</strong></sub>'
        f'<h3>{title_markup(project)}</h3>'
        f'<p>{h(project.get("description") or "A project in the archive.")}</p>'
        f'<p>{stack_chips(project)}</p>'
        f'<p>{status_line(project)}<br>{external_actions(project)}</p>'
        "</td>\n</tr>\n</table>"
    )


def feature_cell(project: dict) -> str:
    return (
        '<td width="50%" valign="top">'
        f'{cover_markup(project, "100%")}'
        f'<br><sub><strong>{eyebrow(project)}</strong></sub>'
        f'<h3>{title_markup(project)}</h3>'
        f'<p>{h(project.get("description") or "A project in the archive.")}</p>'
        f'<p>{stack_chips(project, 4)}</p>'
        f'<p>{status_line(project)}<br>{external_actions(project)}</p>'
        "</td>"
    )


def feature_grid(projects: list[dict]) -> str:
    if not projects:
        return ""
    rows: list[str] = []
    for index in range(0, len(projects), 2):
        cells = [feature_cell(p) for p in projects[index:index + 2]]
        if len(cells) == 1:
            cells.append('<td width="50%"></td>')
        rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")
    return '<table width="100%">\n' + "\n".join(rows) + "\n</table>"


def archive_table(projects: list[dict], featured_ids: set) -> str:
    rows: list[str] = []
    for project in projects:
        star = " ★" if project.get("id") in featured_ids else ""
        rows.append(
            "<tr>\n"
            f'<td width="190" valign="top">{cover_markup(project, "190")}</td>\n'
            '<td valign="top">'
            f'<strong>{title_markup(project)}</strong>{star}<br>{status_line(project)}'
            f'<br>{h(project.get("description") or "A project in the archive.")}'
            f'<br>{stack_chips(project, 4)}'
            f'<br>{external_actions(project)}</td>\n'
            "</tr>"
        )
    return '<table width="100%">\n' + "\n".join(rows) + "\n</table>"


def stat_cell(value: int, label: str) -> str:
    return f'<td align="center" width="25%"><strong>{value}</strong><br><sub>{label}</sub></td>'


def build_readme(projects: list[dict]) -> str:
    if any(not isinstance(p, dict) for p in projects):
        raise ValueError("projects.json must contain only project objects.")
    ids = [p.get("id") for p in projects]
    if len(ids) != len(set(ids)):
        raise ValueError("Project IDs must be unique before README generation.")

    categories: dict[str, list[dict]] = defaultdict(list)
    for project in projects:
        categories[str(project.get("category") or "Uncategorized")].append(project)
    ordered = [c for c in CATEGORY_ORDER if c in categories] + sorted(c for c in categories if c not in CATEGORY_ORDER)
    public_count = sum(p.get("sourceAccess") == "public" and bool(safe_source(p)) for p in projects)
    hidden_count = sum(p.get("sourceAccess") == "hidden" for p in projects)
    live_count = sum(bool(safe_https(p.get("liveUrl"))) for p in projects)
    updated = max((str(p.get("updated") or "") for p in projects), default="") or "Not listed"
    year = datetime.now(timezone.utc).year
    copyright_text = f"© {year} {OWNER}"

    featured = sorted(
        (p for p in projects if p.get("featured")),
        key=lambda p: (str(p.get("updated") or ""), str(p.get("title") or "").casefold()),
        reverse=True,
    )[:FEATURED_LIMIT]
    featured_ids = {p["id"] for p in featured}

    category_nav = " &nbsp;·&nbsp; ".join(
        f'<a href="#{slug(c)}">{h(c)}</a>&nbsp;<sub>{len(categories[c])}</sub>' for c in ordered
    )

    lines = [
        BEGIN,
        '<div align="center">',
        '<img src="assets/brand/readme-banner.svg" alt="My Awesome Projects — built to solve, made to explore" width="100%">',
        "",
        "<p><strong>A curated archive of software, security tooling, product experiments and creative computing.</strong></p>",
        f'<p><a href="{h(SITE_URL)}"><strong>Interactive showcase ↗</strong></a> &nbsp;·&nbsp; <a href="{h(PROFILE_URL)}">GitHub profile ↗</a></p>',
        '<p><sub><a href="#selected-work">Selected work</a> &nbsp;·&nbsp; <a href="#the-archive">The archive</a> &nbsp;·&nbsp; <a href="#source-privacy--live-preview-policy">Source &amp; preview policy</a></sub></p>',
        "",
        "<table>",
        "<tr>",
        stat_cell(len(projects), "PROJECTS"),
        stat_cell(len(categories), "DISCIPLINES"),
        stat_cell(public_count, "PUBLIC SOURCES"),
        stat_cell(live_count, "LIVE PREVIEWS"),
        "</tr>",
        "</table>",
        "</div>",
        "",
        "> Covers are portfolio artwork, not claims that every project is production-ready, and not always real UI screenshots. "
        "A **live preview** and a **public source** are separate things: each link appears only when it has been approved for public visitors.",
        "",
    ]
    if featured:
        lines.extend(["## Selected work", "", lead_card(featured[0]), ""])
        if len(featured) > 1:
            lines.extend([feature_grid(featured[1:]), ""])
    lines.extend([
        "## The archive",
        "",
        f"<p align=\"center\">{category_nav}</p>",
        "",
        f"<p align=\"center\"><sub>★ marks a project also shown in Selected work. "
        f"{plural(len(projects), 'project')} in total, {hidden_count} with source hidden. "
        f"Latest recorded catalog update: {h(updated)}.</sub></p>",
        "",
    ])
    for category in ordered:
        entries = sorted(categories[category], key=lambda p: str(p.get("title") or "").casefold())
        lines.extend([
            f"### {category}", "",
            f"<sub>{plural(len(entries), 'project')} &nbsp;·&nbsp; <a href=\"#the-archive\">Back to archive index ↑</a></sub>", "",
            archive_table(entries, featured_ids), "",
        ])
    lines.extend([
        "---",
        "",
        "## Source privacy & live preview policy",
        "",
        "Private repository code is not mirrored here. For a source-hidden entry, the catalog keeps <code>sourceUrl</code> empty; no source button or source link is generated. Its public live URL may still be displayed independently after anonymous access and deployment safety are verified.",
        "",
        "For deliberately vulnerable labs, internal dashboards, or systems containing real data, do not publish a preview until isolation, synthetic data, access controls and exposed routes have been reviewed.",
        "",
        '<div align="center">',
        f'<p><a href="{h(SITE_URL)}"><strong>Explore the full interactive showcase ↗</strong></a> &nbsp;·&nbsp; <a href="{h(PROFILE_URL)}">GitHub profile ↗</a></p>',
        f"<p><sub><strong>Browse:</strong> {category_nav}</sub></p>",
        '<p><sub><a href="docs/PRIVATE_PROJECTS.md">Private-project policy</a> · <a href="docs/ASSET_GUIDELINES.md">Asset guidelines</a> · <a href="docs/PROJECT_CATALOG.md">Catalog notes</a> · <a href="docs/SITE.md">Website guide</a></sub></p>',
        f"<p><sub>{h(copyright_text)} · {plural(len(projects), 'project')} · {plural(live_count, 'live preview')} · {plural(public_count, 'public source')} · Latest catalog update: {h(updated)}</sub></p>",
        '<p><sub>Catalog source: projects.json · README generated by scripts/generate_readme.py · Public repository sync never imports private repository metadata.</sub></p>',
        "</div>",
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
