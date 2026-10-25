#!/usr/bin/env python3
"""Safely reconcile the public showcase with public GitHub repository metadata.

Only public repositories owned by TARGET_OWNER are considered. Private projects
are intentionally a manual catalog workflow and this script never queries a
credential that can enumerate private repositories.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "projects.json"
TARGET_OWNER = "itssourov13"
SHOWCASE_REPO = "my-awesome-projects"
PROFILE_REPO = TARGET_OWNER
API_ROOT = "https://api.github.com"
USER_AGENT = "my-awesome-projects-public-catalog-sync"
PER_PAGE = 100
MAX_PAGES = 100


class SyncError(RuntimeError):
    """Raised when the public inventory cannot be verified completely."""


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def slug_id(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "github-project"


def date_from_github(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return None


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def activity_status(pushed_at: str | None, archived: bool) -> str:
    if archived:
        return "Archived"
    pushed = date_from_github(pushed_at)
    if not pushed:
        return "Public repository"
    age = (utc_today() - datetime.fromisoformat(pushed).date()).days
    if age <= 30:
        return "Active development"
    if age <= 90:
        return "Recent activity"
    if age <= 365:
        return "Maintained"
    return "Quiet · last push over a year ago"


def category_for(repo: dict) -> str:
    topics = {str(topic).casefold() for topic in (repo.get("topics") or [])}
    name = str(repo.get("name") or "").casefold()
    description = str(repo.get("description") or "").casefold()
    words = topics | set(re.findall(r"[a-z0-9-]+", f"{name} {description}"))
    if words & {"cybersecurity", "security", "pentest", "penetration-testing", "vulnerability", "infosec", "red-team", "blue-team", "ctf", "malware", "reverse-engineering"}:
        return "Cybersecurity"
    if words & {"ai", "artificial-intelligence", "llm", "agent", "agents", "chatbot", "machine-learning", "developer-tools"}:
        return "AI & Developer Tools"
    if words & {"threejs", "three-js", "webgl", "3d", "architecture", "creative-coding", "creative-computing", "animation"}:
        return "Creative & 3D"
    if words & {"android", "mobile", "ios", "flutter", "react-native"}:
        return "Mobile Apps"
    if words & {"blog", "writing", "publishing", "notes", "documentation"}:
        return "Writing & Publishing"
    if words & {"awesome-list", "awesome-lists", "open-source", "opensource"}:
        return "Open Source"
    if words & {"utility", "utilities", "calculator", "planner", "weather", "commute", "converter"}:
        return "Utilities"
    return "Web Apps"


def is_public_repository(repo: dict) -> bool:
    """Fail-closed guard shared by both API ingestion and catalog reconciliation."""
    if not isinstance(repo, dict):
        return False
    owner = str((repo.get("owner") or {}).get("login") or "")
    full_name = str(repo.get("full_name") or "")
    private = repo.get("private")
    visibility = repo.get("visibility")
    parsed = urlparse(str(repo.get("html_url") or ""))
    if owner.casefold() != TARGET_OWNER.casefold():
        return False
    if "/" not in full_name or full_name.split("/", 1)[0].casefold() != TARGET_OWNER.casefold():
        return False
    if private is True or visibility == "private":
        return False
    if visibility not in (None, "public") or private not in (False, None):
        return False
    return parsed.scheme == "https" and parsed.netloc.casefold() == "github.com"


def fetch_public_repositories() -> list[dict]:
    """Fetch every public repository page before allowing reconciliation."""
    repositories: list[dict] = []
    seen: set[str] = set()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    for page in range(1, MAX_PAGES + 1):
        url = (
            f"{API_ROOT}/users/{TARGET_OWNER}/repos"
            f"?type=owner&sort=pushed&direction=desc&per_page={PER_PAGE}&page={page}"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=25) as response:
                if response.status != 200:
                    raise SyncError(f"GitHub returned HTTP {response.status} for public repository inventory.")
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise SyncError(f"GitHub public inventory request failed with HTTP {exc.code}; catalog was not changed.") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SyncError(f"Could not verify the full public GitHub inventory; catalog was not changed: {exc}") from exc

        if not isinstance(payload, list):
            raise SyncError("GitHub repository inventory was not an array; catalog was not changed.")
        for repo in payload:
            if not isinstance(repo, dict):
                raise SyncError("GitHub returned an invalid repository record; catalog was not changed.")
            full_name = str(repo.get("full_name") or "")
            # Defense in depth: explicit allow-list. Never serialize private metadata.
            if not is_public_repository(repo):
                continue
            canonical = f"{TARGET_OWNER}/{full_name.split('/', 1)[1]}"
            key = canonical.casefold()
            if key in seen:
                continue
            repo["full_name"] = canonical
            repo["html_url"] = f"https://github.com/{canonical}"
            seen.add(key)
            repositories.append(repo)
        if len(payload) < PER_PAGE:
            return repositories
    raise SyncError(f"Public repository inventory exceeded {MAX_PAGES} pages; catalog was not changed.")


def repo_name_from_project(project: dict) -> str | None:
    known = project.get("githubRepo")
    if isinstance(known, str) and known.strip():
        return known.strip()
    source_url = project.get("sourceUrl", "")
    try:
        parsed = urlparse(source_url)
        parts = [part for part in parsed.path.split("/") if part]
        if parsed.netloc.casefold() == "github.com" and len(parts) >= 2 and parts[0].casefold() == TARGET_OWNER.casefold():
            return parts[1].removesuffix(".git")
    except (AttributeError, TypeError):
        return None
    return None


def new_project(repo: dict, used_ids: set[str]) -> dict:
    name = str(repo["name"])
    project_id = slug_id(name)
    if project_id in used_ids:
        project_id = f"{project_id}-repo"
    if project_id in used_ids:
        raise SyncError(f"Cannot derive a unique catalog ID for public repository {repo['full_name']}.")
    category = category_for(repo)
    description = str(repo.get("description") or "").strip()
    if not description:
        description = f"Public GitHub repository by @{TARGET_OWNER}; add a curated project summary when reviewing this entry."
    language = repo.get("language")
    stack = [str(language)] if isinstance(language, str) and language.strip() else ["Not specified"]
    updated = date_from_github(repo.get("pushed_at")) or utc_today().isoformat()
    return {
        "id": project_id,
        "title": name.replace("-", " ").replace("_", " ").strip().title(),
        "eyebrow": f"{category.upper()} · PUBLIC REPOSITORY",
        "category": category,
        "description": description[:500],
        "story": "Automatically discovered from the owner's public GitHub repository metadata. Curate this summary before adding claims about features or production readiness.",
        "highlights": ["Public source repository", "Repository metadata synced from GitHub"],
        "stack": stack,
        "sourceAccess": "public",
        "sourceUrl": repo["html_url"],
        "liveUrl": "",
        "demoLabel": "",
        "demoNote": "No live deployment is linked automatically. Add a public HTTPS preview only after verifying anonymous access and safety.",
        "status": activity_status(repo.get("pushed_at"), bool(repo.get("archived"))),
        "featured": False,
        "updated": updated,
        "githubRepo": repo["name"],
        "syncMode": "github",
        "cover": f"assets/projects/{project_id}/cover.svg",
        "screenshots": [],
        "gallery": [],
    }


def sync_catalog(projects: list[dict], repositories: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Apply verified public metadata and preserve manually curated/private entries."""
    # Re-check at the reconciliation boundary too; this function must not
    # depend on its caller having already filtered API records correctly.
    repositories = [repo for repo in repositories if is_public_repository(repo)]
    public_by_name = {str(repo["name"]).casefold(): repo for repo in repositories}
    normalized_titles = {normalize(str(project.get("id") or "")) for project in projects}
    normalized_titles.update(normalize(str(project.get("title") or "")) for project in projects)
    used_ids = {str(project.get("id") or "") for project in projects}
    updated_existing = 0
    hidden_source_links = 0
    added = 0

    for project in projects:
        repo_name = repo_name_from_project(project)
        if not repo_name:
            continue
        repo = public_by_name.get(repo_name.casefold())
        if repo:
            # A manually hidden entry remains hidden. Only public source-linked entries
            # are matched here; hidden records may represent private or unpublished work.
            if project.get("sourceAccess") == "public":
                project["githubRepo"] = str(repo["name"])
                project["sourceUrl"] = str(repo["html_url"])
                pushed = date_from_github(repo.get("pushed_at"))
                if pushed and project.get("updated") != pushed:
                    project["updated"] = pushed
                    updated_existing += 1
                if project.get("syncMode") == "github":
                    # GitHub-generated entries may follow public metadata; curated entries do not.
                    project["title"] = str(repo.get("name") or project["title"]).replace("-", " ").replace("_", " ").strip().title()
                    project["description"] = str(repo.get("description") or "").strip()[:500] or f"Public GitHub repository by @{TARGET_OWNER}."
                    project["stack"] = [repo["language"]] if isinstance(repo.get("language"), str) and repo["language"].strip() else ["Not specified"]
                    project["category"] = category_for(repo)
                    project["eyebrow"] = f"{project['category'].upper()} · PUBLIC REPOSITORY"
                    project["status"] = activity_status(repo.get("pushed_at"), bool(repo.get("archived")))
            elif project.get("sourceAccess") == "hidden":
                # Never turn a manually hidden/possibly private source into a public link.
                continue
        elif project.get("sourceAccess") == "public":
            # Fail closed if an owned repository is deleted, renamed, or no longer public.
            parsed = urlparse(str(project.get("sourceUrl") or ""))
            if parsed.netloc.casefold() == "github.com" and parsed.path.strip("/").split("/")[0:1] == [TARGET_OWNER]:
                project["sourceAccess"] = "hidden"
                project["sourceUrl"] = ""
                project.pop("githubRepo", None)
                hidden_source_links += 1

    # Discover public repos not represented by either a source-linked entry or an intentional
    # curated hidden entry. Normalize names so "scholarhub" doesn't duplicate "scholar-hub".
    existing_repo_names = {
        (repo_name_from_project(project) or "").casefold()
        for project in projects
        if project.get("sourceAccess") == "public"
    }
    existing_normalized = set(normalized_titles)
    for repo in repositories:
        name = str(repo["name"])
        full_name = str(repo["full_name"])
        if name.casefold() in {SHOWCASE_REPO.casefold(), PROFILE_REPO.casefold()}:
            continue
        if name.casefold() in existing_repo_names:
            continue
        normalized_name = normalize(name)
        if normalized_name in existing_normalized:
            continue
        project = new_project(repo, used_ids)
        projects.append(project)
        used_ids.add(project["id"])
        existing_repo_names.add(name.casefold())
        existing_normalized.add(normalized_name)
        existing_normalized.add(normalize(project["title"]))
        added += 1

    stats = {
        "public_repositories_verified": len(repositories),
        "curated_entries_preserved": len(projects) - added,
        "new_public_entries": added,
        "updated_existing_entries": updated_existing,
        "source_links_hidden_for_safety": hidden_source_links,
    }
    return projects, stats


def main() -> int:
    try:
        original = json.loads(CATALOG.read_text(encoding="utf-8"))
        if not isinstance(original, list) or any(not isinstance(item, dict) for item in original):
            raise SyncError("projects.json must contain an array of project objects.")
        # Inventory first; no local files are mutated if API fetch is incomplete.
        repositories = fetch_public_repositories()
        # Exclude only the repository hosting this catalog. Keep the profile
        # repository in the verified inventory so its existing curated entry
        # retains a source link; it is excluded from new-entry discovery below.
        repositories = [
            repo for repo in repositories
            if str(repo.get("name") or "").casefold() != SHOWCASE_REPO.casefold()
        ]
        projects, stats = sync_catalog(original, repositories)
        CATALOG.write_text(json.dumps(projects, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, SyncError) as exc:
        print(f"PUBLIC SYNC FAILED: {exc}", file=sys.stderr)
        return 1
    print("Public project catalog sync")
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ')}: {value}")
    print("  Private projects: manual-only; no private inventory was requested or published.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
