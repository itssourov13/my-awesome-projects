#!/usr/bin/env python3
"""Collect public artwork for showcase covers; save optimized, local source images."""
from __future__ import annotations

import concurrent.futures
import html.parser
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "projects.json"
SOURCE_LOG = ROOT / "assets/artwork-sources.json"
OWNER = "itssourov13"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
MIN_WIDTH, MIN_HEIGHT = 620, 350
OUT_SIZE = (1600, 1000)
MAX_BYTES = 16 * 1024 * 1024
FORCE_SCREENSHOT = {"personal-website-test", "claude-personal-website", "birthday-present-preview", "hackergf-ai", "cinematic-architecture-web", "arven", "stele-residences", "itssourov13"}

# Publicly accessible image files found through public web image search.
# They are used only when a project doesn't provide a suitable public page image.
# Source/page URLs are retained in assets/artwork-sources.json.
FALLBACK_ARTWORK = {
    "apk-sherlock": ("https://approov.io/blog/how-to-extract-an-api-key-from-a-mobile-app-with-static-binary-analysis", "https://approov.io/hubfs/Screenshot%20from%202019-02-22%2015-14-22.png", "public-web-reference"),
    "ares": ("https://corgea.com/blog/introducing-ai-pentesting", "https://corgea.com/cms/blog/introducing-ai-pentesting/image-3.png", "public-web-reference"),
    "cyberos": ("https://dribbble.com/shots/26782942-Cyber-Security-Monitoring-Dashboard", "https://cdn.dribbble.com/userupload/45736838/file/still-2ee034cefe9394c177601ebe88faf1ae.png?resize=1600x1200", "public-web-reference"),
    "passhunter": ("https://x.com/DailyDarkWeb/status/1750806774356033865", "https://pbs.twimg.com/media/GEwcsskWQAAIM0F.jpg", "public-web-reference"),
    "personal-website-pentest": ("https://dribbble.com/shots/26618504-Anarisk-Cyber-Security-Dashboard", "https://cdn.dribbble.com/userupload/45207896/file/640ac0444ba6f410c58f3a2f683ec2d0.png?resize=1200x900&vertical=center", "public-web-reference"),
    "uab": ("https://www.lunar.dev/post/march-update", "https://cdn.prod.website-files.com/649c330ec64b4a2c43b6fa63/65eb82fe968a8f6d572185b6_Yt3A681baSEGJ3pWkHo7oDGM8ng1g3aW1I-EO3PDPFcmHy6LJJUWAFYBVBnjli47pSAiqmQe15lw8vjq7D68by8LJFAh44GexsNSaBNiErlK1Qz94lTU8rlHv1eeczes3lGlo6d3IYsxIueMZPMyqI4.png", "public-web-reference"),
    "VercelStrike": ("https://aws.amazon.com/marketplace/pp/prodview-yaj7evoeiuoxq", "https://d7umqicpi7263.cloudfront.net/promotionalMedia/444f766ac6e1dd70c15bd5d15de100ff", "public-web-reference"),
    "VercStorm": ("https://www.dedoimedo.com/computers/lynis.html", "https://www.dedoimedo.com/images/computers-years/2024-1/lynis-results-root.png", "public-web-reference"),
    "hackerai-main": ("https://defendlab.com/", "https://defendlab.com/assets/hero-dashboard.png", "public-web-reference"),
    "hackerai-base44": ("https://dribbble.com/shots/26193634-Reimagined-AI-based-IDE-Code-terminal-editor", "https://cdn.dribbble.com/userupload/43840196/file/original-0720d32584c00913abe3757b9aa0fcdf.png?resize=1200x900", "public-web-reference"),
    "rise-of-ai": ("https://www.awwwards.com/inspiration/creative-3d-website-submission-687b73ea18842090638416", "https://assets.awwwards.com/awards/element/2025/07/687f8a332095e955842559.png", "public-web-reference"),
    "active-theory": ("https://labs.anvil-ai.io/demos/2026-02-21/concept-01-helios-constellation-reactor/", "https://labs.anvil-ai.io/demos/2026-02-21/concept-01-helios-constellation-reactor/thumbnail.png", "public-web-reference"),
    "travel-weather-planner": ("https://devpost.com/software/travel-planner-itinerary-builder", "https://d112y698adiu2z.cloudfront.net/photos/production/software_photos/003/470/091/datas/original.png", "public-web-reference"),
    "Employee-profile-generator": ("https://www.sourcecodester.com/php/14917/online-id-generator-system-using-php-free-source-code.html", "https://www.sourcecodester.com/sites/default/files/images/oretnom23/template_editor.png", "public-web-reference"),
    "Report-card-printer": ("https://klasmart.com/feature/e-rapor", "https://klasmart.com/images/feature/548172627920250730115926_640.png", "public-web-reference"),
    "Movie-Ticket-Booking-Calculator-Python-": ("https://medium.com/@janavi.mehta2003/from-seat-selection-to-receipt-building-a-movie-booking-console-in-python-9b848cba2fea", "https://miro.medium.com/v2/resize%3Afit%3A1400/1%2AVuquop_PM37F1wc7w61oow.png", "public-web-reference"),
    "awesome": ("https://git-history.com/", "https://git-history.com/og-image.png", "public-web-reference"),
    "cinematic-architecture-web": ("https://www.behance.net/gallery/225639379/Industrial-Design-Portfolio?l=123", "https://mir-s3-cdn-cf.behance.net/project_modules/1400_webp/c6b617225639379.68212ee508c1f.png", "public-web-reference"),
    "stele-residences": ("https://www.joeadsett.com.au/toowoomba", "https://images.squarespace-cdn.com/content/v1/63489f943c8fe05f05ed325a/1670289024954-36JLTXMSUBJS3PW78XEN/JAA_Cliffhanger_CamMurchison-78.jpg?format=2500w", "public-web-reference"),
    "personal-website-test": ("https://rojishbhurtel.com.np/", "https://rojishbhurtel.com.np/uploads/ai/ai_portfolio_gen.png", "public-web-reference"),
    "birthday-present-preview": ("https://cinematiccard.com/blog/virtual-birthday-cards", "https://cinematiccard.com/assets/blog-img/themes/birthday-her-luxury.webp", "public-web-reference"),
    "create-present-website": ("https://vishalchauhan.in/projects/giftfeels", "https://vishalchauhan.in/_next/image?q=75&url=%2Fproject%2Fgiftfeels.png&w=3840", "public-web-reference"),
    "study-planner-apk": ("https://dribbble.com/shots/27315427-AI-Study-Assistant-App", "https://cdn.dribbble.com/userupload/47512714/file/186f7d5fef412696cc793396e167022b.png?resize=1200x900&vertical=center", "public-web-reference"),
    "js.org": ("https://js.org", "https://js.org/jsorg_ogimage.png", "public-web-reference"),
}
PREFER_FALLBACK_FIRST = {
    "cinematic-architecture-web", "stele-residences", "personal-website-test",
    "birthday-present-preview", "create-present-website", "study-planner-apk", "js.org",
}

class MetaParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.og_image = ""
        self.title = False
        self.title_text = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "meta":
            key = (attrs.get("property") or attrs.get("name") or "").lower()
            if key in {"og:image", "twitter:image", "twitter:image:src"} and attrs.get("content") and not self.og_image:
                self.og_image = attrs["content"].strip()
        elif tag.lower() == "title":
            self.title = True
    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.title = False
    def handle_data(self, data):
        if self.title:
            self.title_text.append(data.strip())

def request_bytes(url: str, limit: int = MAX_BYTES) -> tuple[bytes, str]:
    if not url.startswith("https://"):
        raise ValueError("Only HTTPS sources are allowed.")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"})
    with urlopen(request, timeout=22) as response:
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type", "").lower()
        if not final_url.startswith("https://"):
            raise ValueError("Redirected away from HTTPS.")
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Image exceeds size limit.")
        return data, content_type

def valid_image(data: bytes) -> Image.Image:
    from io import BytesIO
    im = Image.open(BytesIO(data))
    im.load()
    if im.width < MIN_WIDTH or im.height < MIN_HEIGHT:
        raise ValueError(f"Image too small: {im.width}x{im.height}")
    if im.width > 10000 or im.height > 10000:
        raise ValueError(f"Image has unreasonable dimensions: {im.width}x{im.height}")
    return ImageOps.exif_transpose(im)

def find_og_image(page_url: str) -> tuple[str, str]:
    data, _ = request_bytes(page_url, limit=2 * 1024 * 1024)
    parser = MetaParser()
    parser.feed(data.decode("utf-8", "replace"))
    title = " ".join(parser.title_text).strip()
    if not parser.og_image:
        return "", title
    return urljoin(page_url, parser.og_image), title

def screenshot_url(url: str, output: Path) -> bool:
    chromium = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if not chromium:
        return False
    command = [
        chromium, "--headless=new", "--no-sandbox", "--disable-gpu",
        "--disable-dev-shm-usage", "--disable-extensions", "--hide-scrollbars",
        "--window-size=1600,1000", "--virtual-time-budget=7000",
        f"--screenshot={output}", url,
    ]
    try:
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=35, check=False)
        if result.returncode != 0 or not output.is_file():
            return False
        with Image.open(output) as im:
            if im.width < MIN_WIDTH or im.height < MIN_HEIGHT:
                output.unlink(missing_ok=True)
                return False
        return True
    except (subprocess.TimeoutExpired, OSError):
        output.unlink(missing_ok=True)
        return False

def repo_readme_image(project: dict) -> tuple[str, str] | None:
    source = project.get("sourceUrl", "")
    parsed = urlparse(source)
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if parsed.netloc.lower() not in {"github.com", "www.github.com"} or len(parts) < 2 or parts[0].lower() != OWNER.lower():
        return None
    repo = parts[1]
    for branch in ("HEAD", "main", "master"):
        readme_url = f"https://raw.githubusercontent.com/{OWNER}/{repo}/{branch}/README.md"
        try:
            raw, _ = request_bytes(readme_url, limit=2 * 1024 * 1024)
            text = raw.decode("utf-8", "replace")
            candidates = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
            candidates += re.findall(r'<img[^>]+src=["\']([^"\']+)', text, re.I)
            for candidate in candidates:
                candidate = candidate.strip().strip("<>")
                if not candidate or candidate.startswith("data:"):
                    continue
                if any(x in candidate.lower() for x in ("shields.io", "img.shields", "badge", "visitor-badge", "github.com/actions")):
                    continue
                candidate = candidate.split(" ")[0].strip()
                if candidate.startswith("//"):
                    candidate = "https:" + candidate
                elif not candidate.startswith("https://"):
                    candidate = f"https://raw.githubusercontent.com/{OWNER}/{repo}/{branch}/{candidate.lstrip('./')}"
                try:
                    data, _ = request_bytes(candidate)
                    valid_image(data)
                    return candidate, readme_url
                except Exception:
                    continue
        except Exception:
            continue
    return None

def save_normalized(data: bytes, output: Path) -> tuple[int, int]:
    from io import BytesIO
    with Image.open(BytesIO(data)) as opened:
        if opened.width < MIN_WIDTH or opened.height < MIN_HEIGHT:
            raise ValueError(f"Image too small: {opened.width}x{opened.height}")
        if opened.width > 10000 or opened.height > 10000:
            raise ValueError(f"Image has unreasonable dimensions: {opened.width}x{opened.height}")
        image = ImageOps.exif_transpose(opened)
        if image.mode in ("RGBA", "LA") or "transparency" in image.info:
            rgba = image.convert("RGBA")
            background = Image.new("RGBA", rgba.size, "#101318")
            background.alpha_composite(rgba)
            image = background.convert("RGB")
        else:
            image = image.convert("RGB")
        image = ImageOps.fit(image, OUT_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output, format="JPEG", quality=91, optimize=True, progressive=True, subsampling=0)
        return image.width, image.height

def collect_one(project: dict) -> dict:
    project_id = str(project["id"])
    source_path = ROOT / "assets" / "projects" / project_id / "source" / "cover.jpg"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    page_url = ""
    image_url = ""
    source_kind = ""
    title = ""
    errors: list[str] = []

    if project_id in PREFER_FALLBACK_FIRST and project_id in FALLBACK_ARTWORK:
        page_url, image_url, source_kind = FALLBACK_ARTWORK[project_id]
        data, _ = request_bytes(image_url)
        save_normalized(data, source_path)
        return {"id": project_id, "title": project.get("title"), "pageUrl": page_url, "imageUrl": image_url, "kind": source_kind, "imagePath": str(source_path.relative_to(ROOT)), "status": "downloaded", "notes": ["Selected a high-resolution public reference visual because the live-site capture path was unreliable."]}

    live_url = str(project.get("liveUrl") or "").strip()
    if live_url:
        if project_id not in FORCE_SCREENSHOT:
            try:
                image_url, title = find_og_image(live_url)
                if image_url:
                    try:
                        data, _ = request_bytes(image_url)
                        save_normalized(data, source_path)
                        page_url, source_kind = live_url, "project-page-open-graph"
                        return {"id": project_id, "title": project.get("title"), "pageUrl": page_url, "imageUrl": image_url, "kind": source_kind, "imagePath": str(source_path.relative_to(ROOT)), "pageTitle": title, "status": "downloaded"}
                    except Exception as exc:
                        errors.append("og-image: " + str(exc)[:160])
            except Exception as exc:
                errors.append("og-parse: " + str(exc)[:160])
        with tempfile.TemporaryDirectory(prefix="showcase-art-") as tmp:
            screenshot = Path(tmp) / "public-live-page.png"
            if screenshot_url(live_url, screenshot):
                try:
                    with Image.open(screenshot) as im:
                        im = ImageOps.exif_transpose(im).convert("RGB")
                        im = ImageOps.fit(im, OUT_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.25))
                        im.save(source_path, format="JPEG", quality=91, optimize=True, progressive=True, subsampling=0)
                    return {"id": project_id, "title": project.get("title"), "pageUrl": live_url, "imageUrl": live_url, "kind": "public-live-site-screenshot", "imagePath": str(source_path.relative_to(ROOT)), "pageTitle": title, "status": "screenshot", "notes": errors}
                except Exception as exc:
                    errors.append("screenshot-process: " + str(exc)[:160])

    if project_id not in FORCE_SCREENSHOT:
        found = repo_readme_image(project)
        if found:
            image_url, page_url = found
            try:
                data, _ = request_bytes(image_url)
                save_normalized(data, source_path)
                return {"id": project_id, "title": project.get("title"), "pageUrl": page_url, "imageUrl": image_url, "kind": "public-repository-readme-image", "imagePath": str(source_path.relative_to(ROOT)), "status": "downloaded", "notes": errors}
            except Exception as exc:
                errors.append("repo-image: " + str(exc)[:160])

    if project_id in FALLBACK_ARTWORK:
        page_url, image_url, source_kind = FALLBACK_ARTWORK[project_id]
        try:
            data, _ = request_bytes(image_url)
            save_normalized(data, source_path)
            return {"id": project_id, "title": project.get("title"), "pageUrl": page_url, "imageUrl": image_url, "kind": source_kind, "imagePath": str(source_path.relative_to(ROOT)), "status": "downloaded", "notes": errors}
        except Exception as exc:
            errors.append("public-web-reference: " + str(exc)[:160])

    source_url = str(project.get("sourceUrl") or "").strip()
    if source_url and source_url.startswith("https://github.com/"):
        with tempfile.TemporaryDirectory(prefix="showcase-art-repo-") as tmp:
            screenshot = Path(tmp) / "public-repo-page.png"
            if screenshot_url(source_url, screenshot):
                try:
                    with Image.open(screenshot) as im:
                        im = ImageOps.fit(im.convert("RGB"), OUT_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.25))
                        im.save(source_path, format="JPEG", quality=90, optimize=True, progressive=True)
                    return {"id": project_id, "title": project.get("title"), "pageUrl": source_url, "imageUrl": source_url, "kind": "public-repository-page-screenshot", "imagePath": str(source_path.relative_to(ROOT)), "status": "screenshot", "notes": errors}
                except Exception as exc:
                    errors.append("repo-screenshot: " + str(exc)[:160])

    return {"id": project_id, "title": project.get("title"), "status": "failed", "errors": errors + ["No suitable public image source found."]}

def main() -> int:
    projects = json.loads(CATALOG.read_text(encoding="utf-8"))
    existing = []
    if SOURCE_LOG.exists():
        try:
            existing = json.loads(SOURCE_LOG.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []
    results_by_id = {item.get("id"): item for item in existing if item.get("id")}

    selected = set()
    missing_only = len(sys.argv) > 1 and sys.argv[1] == "--missing"
    if len(sys.argv) > 1 and sys.argv[1] == "--only":
        selected = {value.strip() for value in ",".join(sys.argv[2:]).split(",") if value.strip()}
        unknown = selected - {str(project["id"]) for project in projects}
        if unknown:
            print("Unknown project IDs: " + ", ".join(sorted(unknown)), file=sys.stderr)
            return 2
        projects = [project for project in projects if str(project["id"]) in selected]

    def stored_source_path(project: dict) -> Path:
        project_id = str(project["id"])
        metadata = results_by_id.get(project_id, {})
        relative = metadata.get("imagePath") or f"assets/projects/{project_id}/source/cover.jpg"
        relative_path = Path(str(relative))
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"Unsafe artwork source path for {project_id}: {relative}")
        return ROOT / relative_path

    if missing_only:
        projects = [project for project in projects if not stored_source_path(project).is_file()]
        if not projects:
            print("No project artwork missing; existing source images remain unchanged.")
            return 0

    # A manually supplied banner is an explicit owner choice. Keep it on both
    # full refreshes and targeted refreshes; automatic scraping must not replace it.
    pending = []
    for project in projects:
        project_id = str(project["id"])
        metadata = results_by_id.get(project_id, {})
        if metadata.get("kind") == "user-provided-banner":
            source = stored_source_path(project)
            if not source.is_file():
                print(f"ERROR: owner-provided banner source missing for {project_id}: {source}", file=sys.stderr)
                return 1
            print(f"PRESERVED   {project_id}: owner-provided banner {metadata.get('imagePath', '')}")
            continue
        pending.append(project)
    projects = pending
    if not projects:
        print("No artwork requires collection; owner-provided banner(s) preserved.")
        return 0

    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(collect_one, project): project for project in projects}
        for future in concurrent.futures.as_completed(futures):
            project = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"id": project.get("id"), "title": project.get("title"), "status": "failed", "errors": [str(exc)[:200]]}
            results.append(result)
            print(f"{result['status'].upper():10s} {result['id']}: {result.get('kind', '')} {result.get('errors', result.get('notes', []))}")
    results_by_id.update({item["id"]: item for item in results})
    ordered = sorted(results_by_id.values(), key=lambda item: item.get("id", ""))
    SOURCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_LOG.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [result for result in results if result["status"] == "failed"]
    if selected:
        print(f"Artwork refresh complete: {len(results) - len(failed)}/{len(projects)} selected visuals collected.")
    else:
        print(f"Artwork collection complete: {len(results) - len(failed)}/{len(projects)} project visuals collected.")
    if failed:
        print("Failed project IDs: " + ", ".join(result["id"] for result in failed))
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
