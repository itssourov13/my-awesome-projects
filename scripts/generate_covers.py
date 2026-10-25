#!/usr/bin/env python3
"""Generate image-backed, high-resolution project covers from reviewed public artwork."""
from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PALETTES = {
    "Cybersecurity": ("#0a151a", "#143f42", "#d0ff70", "#72c9c7"),
    "AI & Developer Tools": ("#111127", "#39316b", "#c4a9ff", "#73dcff"),
    "Mobile Apps": ("#241b17", "#70452b", "#ffd079", "#f7a58b"),
    "Creative & 3D": ("#171822", "#43314e", "#e7adff", "#82d9e8"),
    "Web Apps": ("#141b2b", "#344a6a", "#c7e7ff", "#8aa7ff"),
    "Writing & Publishing": ("#28251f", "#605444", "#f0d6a3", "#c5cba8"),
    "Open Source": ("#14241b", "#28583c", "#c3f47c", "#89dcb3"),
    "Utilities": ("#171f2c", "#304e67", "#9fd6ff", "#b9f2b5"),
}
FONT_REGULAR = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
)
FONT_BOLD = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (FONT_BOLD if bold else FONT_REGULAR):
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> float:
    return draw.textlength(text, font=fnt)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_width: int, max_lines: int = 3) -> list[str]:
    words = re.sub(r"\s+", " ", str(text or "").strip()).split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or text_width(draw, candidate, fnt) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and text_width(draw, last + "...", fnt) > max_width:
            last = last[:-1].rstrip()
        lines[-1] = last + "..."
    return lines


def draw_wrapped(draw, xy, text, fnt, fill, width, line_gap=10, max_lines=3):
    x, y = xy
    lines = wrap_text(draw, text, fnt, width, max_lines=max_lines)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill, stroke_width=0)
        bbox = draw.textbbox((x, y), line, font=fnt)
        y = bbox[3] + line_gap
    return y


def load_artwork_map() -> dict:
    path = ROOT / "assets/artwork-sources.json"
    if not path.exists():
        return {}
    return {item["id"]: item for item in json.loads(path.read_text(encoding="utf-8")) if item.get("status") != "failed"}


def add_gradient(image: Image.Image, palette: tuple[str, str, str, str]) -> Image.Image:
    width, height = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pix = overlay.load()
    # Strong left-side scrim keeps title legible while leaving the captured art visible on the right.
    for x in range(width):
        ratio = x / max(1, width - 1)
        alpha = int(218 * (1 - ratio) ** 1.55 + 36)
        for y in range(height):
            bottom = max(0, int((y / height - 0.68) * 95))
            pix[x, y] = (7, 10, 15, min(232, alpha + bottom))
    image = Image.alpha_composite(image.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(image, "RGBA")
    accent = palette[2]
    draw.rounded_rectangle((0, 0, width, height), radius=0, outline=(255, 255, 255, 25), width=1)
    draw.line((72, 0, 72, height), fill=(255, 255, 255, 15), width=1)
    return image


def source_label(source: dict) -> str:
    kind = source.get("kind", "")
    if kind == "public-live-site-screenshot":
        return "LIVE SITE VISUAL"
    if kind == "project-page-open-graph":
        return "PROJECT SHARE ART"
    if kind == "public-repository-readme-image":
        return "REPOSITORY VISUAL"
    if kind == "public-web-reference":
        return "PUBLIC WEB REFERENCE"
    return "PROJECT VISUAL"


def raster_cover(project: dict, image_path: Path, out_path: Path, provenance: dict) -> None:
    palette = PALETTES.get(project.get("category", "Web Apps"), PALETTES["Web Apps"])
    c1, c2, accent, accent2 = palette
    with Image.open(image_path) as src:
        original = src.convert("RGB")
        if provenance.get("kind") == "user-provided-banner":
            # Preserve the supplied banner in full; use a softened, darkened fill
            # behind it to meet the gallery's 1200x700 cover ratio without cropping text.
            image = ImageOps.fit(original, (1200, 700), method=Image.Resampling.LANCZOS)
            image = ImageEnhance.Brightness(image.filter(ImageFilter.GaussianBlur(radius=24))).enhance(0.52)
            foreground = ImageOps.contain(original, (1200, 700), method=Image.Resampling.LANCZOS)
            image.paste(foreground, ((1200 - foreground.width) // 2, (700 - foreground.height) // 2))
            out_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(out_path, "WEBP", quality=94, method=6)
            return
        image = ImageOps.fit(original, (1200, 700), method=Image.Resampling.LANCZOS, centering=(0.54, 0.42))
    image = add_gradient(image, palette)
    draw = ImageDraw.Draw(image, "RGBA")

    # Accent strips and discreet editorial metadata.
    draw.rounded_rectangle((72, 54, 83, 65), radius=3, fill=accent)
    eyebrow = str(project.get("eyebrow") or project.get("category") or "PROJECT ARCHIVE").upper()
    draw.text((101, 51), eyebrow[:46], font=font(15, True), fill=(245, 246, 242, 225))
    label = source_label(provenance)
    label_font = font(11, True)
    label_w = int(text_width(draw, label, label_font)) + 30
    draw.rounded_rectangle((1200 - label_w - 62, 44, 1138, 76), radius=16, fill=(7, 12, 18, 140), outline=(255, 255, 255, 55), width=1)
    draw.text((1200 - label_w - 47, 53), label, font=label_font, fill=(242, 245, 239, 190))

    category_y = 142
    draw.text((72, category_y), str(project.get("category", "PROJECT")).upper(), font=font(13, True), fill=accent)
    title = str(project.get("title") or "Untitled project")
    # Fit long titles without making every banner look the same.
    title_size = 62 if len(title) <= 19 else 54 if len(title) <= 28 else 46
    title_font = font(title_size, True)
    title_y = 190
    title_lines = wrap_text(draw, title, title_font, 700, max_lines=2)
    if len(title_lines) == 1 and text_width(draw, title_lines[0], title_font) > 700:
        title_font = font(48, True)
        title_lines = wrap_text(draw, title, title_font, 700, max_lines=2)
    for line in title_lines:
        draw.text((70, title_y), line, font=title_font, fill=(250, 250, 246, 255), stroke_width=1, stroke_fill=(0, 0, 0, 65))
        title_y += title_size + 8

    description = str(project.get("description") or "A project in the My Awesome Projects archive.")
    desc_y = max(355, title_y + 18)
    desc_y = draw_wrapped(draw, (74, desc_y), description, font(18), (229, 233, 235, 236), 635, line_gap=9, max_lines=3)

    # Bottom metadata rail: status and stack are kept legible on wide and narrow crops.
    rail_y = 556
    draw.line((72, rail_y - 22, 640, rail_y - 22), fill=(255, 255, 255, 76), width=1)
    status = str(project.get("status") or "Project archive")
    draw.text((72, rail_y), status[:42], font=font(15, True), fill=accent)
    stack = project.get("stack") if isinstance(project.get("stack"), list) else []
    chips = [str(x) for x in stack[:4] if str(x).strip()]
    chip_x = 72
    chip_y = 602
    for item in chips:
        label_text = item[:22]
        item_font = font(12, True)
        chip_w = int(text_width(draw, label_text, item_font)) + 24
        if chip_x + chip_w > 780:
            break
        draw.rounded_rectangle((chip_x, chip_y, chip_x + chip_w, chip_y + 30), radius=15, fill=(8, 13, 18, 155), outline=(255, 255, 255, 66), width=1)
        draw.text((chip_x + 12, chip_y + 7), label_text, font=item_font, fill=(244, 245, 241, 220))
        chip_x += chip_w + 8
    draw.text((72, 659), "MY AWESOME PROJECTS  /  SOUROV", font=font(10, True), fill=(235, 239, 231, 150))

    # Small accent marker adds a consistent gallery signature without obscuring the image.
    draw.rounded_rectangle((1090, 602, 1138, 650), radius=12, fill=(7, 12, 18, 145), outline=(255, 255, 255, 65), width=1)
    draw.ellipse((1106, 618, 1122, 634), outline=accent, width=2)
    draw.ellipse((1111, 623, 1117, 629), fill=accent2)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(out_path, "WEBP", quality=90, method=6)


def svg_cover(project: dict, index: int) -> str:
    """Original fallback for newly synced public repositories without a usable image yet."""
    category = project.get("category", "Web Apps")
    c1, c2, a1, a2 = PALETTES.get(category, PALETTES["Web Apps"])
    title_lines = str(project.get("title", "Project")).split()
    title_lines = [" ".join(title_lines[:3]), " ".join(title_lines[3:6])] if len(title_lines) > 3 else [" ".join(title_lines)]
    title_lines = [line for line in title_lines if line]
    title_svg = []
    for i, line in enumerate(title_lines[:2]):
        title_svg.append(f'<text x="70" y="{328 + i*61}" fill="#f5f4ed" font-family="system-ui,-apple-system,Segoe UI,sans-serif" font-weight="680" font-size="48">{html.escape(line)}</text>')
    bg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(str(project.get("title","Project")))} — project cover</title>
<desc id="desc">{html.escape(str(project.get("description",""))[:150])}</desc>
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient><radialGradient id="glow"><stop stop-color="{a1}" stop-opacity=".3"/><stop offset="1" stop-color="{a1}" stop-opacity="0"/></radialGradient></defs>
<rect width="1200" height="700" fill="url(#bg)"/><circle cx="1000" cy="80" r="360" fill="url(#glow)"/>
<g opacity=".11" stroke="#fff"><path d="M0 100H1200M0 200H1200M0 300H1200M0 400H1200M0 500H1200M0 600H1200"/><path d="M100 0V700M200 0V700M300 0V700M400 0V700M500 0V700M600 0V700M700 0V700M800 0V700M900 0V700M1000 0V700M1100 0V700"/></g>
<text x="70" y="70" fill="{a1}" font-family="monospace" font-size="14">{html.escape(category.upper())}</text>{''.join(title_svg)}
<text x="70" y="540" fill="#fff" fill-opacity=".82" font-family="system-ui,sans-serif" font-size="18">{html.escape(str(project.get("status","Project archive"))[:55])}</text>
<text x="70" y="655" fill="{a1}" font-family="monospace" font-size="11" letter-spacing="1.5">MY AWESOME PROJECTS / SOUROV</text>
<g transform="translate(900 350)" fill="none" stroke="{a1}" stroke-opacity=".7"><circle r="150"/><ellipse rx="210" ry="78" transform="rotate(-30)"/><ellipse rx="78" ry="210" transform="rotate(30)"/><circle r="45" fill="{a1}" fill-opacity=".2"/></g>
</svg>'''
    return bg


def main() -> None:
    projects = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
    artwork = load_artwork_map()
    for index, project in enumerate(projects, 1):
        project_id = str(project["id"])
        provenance = artwork.get(project_id, {})
        default_source = f"assets/projects/{project_id}/source/cover.jpg"
        source_rel = str(provenance.get("imagePath") or default_source)
        source_part = Path(source_rel)
        if source_part.is_absolute() or ".." in source_part.parts:
            raise ValueError(f"Unsafe artwork source path for {project_id}: {source_rel}")
        source = ROOT / source_part

        if source.is_file() and project_id in artwork:
            default_output = f"assets/projects/{project_id}/cover.webp"
            output_rel = str(provenance.get("coverOutput") or default_output)
            output_part = Path(output_rel)
            if output_part.is_absolute() or ".." in output_part.parts or not output_rel.startswith("assets/projects/"):
                raise ValueError(f"Unsafe cover output path for {project_id}: {output_rel}")
            output = ROOT / output_part
            raster_cover(project, source, output, provenance)
            (ROOT / "assets" / "projects" / project_id / "cover.svg").unlink(missing_ok=True)
            project["cover"] = output_rel
        else:
            target = ROOT / "assets" / "projects" / project_id / "cover.svg"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(svg_cover(project, index), encoding="utf-8")
            project["cover"] = str(target.relative_to(ROOT))

    catalog = ROOT / "projects.json"
    catalog.write_text(json.dumps(projects, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Keep the existing social preview path stable for the repository index itself.
    brand = ROOT / "assets/brand"
    brand.mkdir(parents=True, exist_ok=True)
    favicon = brand / "favicon.svg"
    if not favicon.exists():
        favicon.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="15" fill="#101114"/><rect x="13" y="34" width="9" height="16" rx="3" fill="#c6f56c" opacity=".65"/><rect x="27" y="16" width="9" height="34" rx="3" fill="#c6f56c"/><rect x="41" y="25" width="9" height="25" rx="3" fill="#c6f56c" opacity=".8"/></svg>', encoding="utf-8")
    generated = sum(
        (ROOT / str(artwork.get(str(project["id"]), {}).get("imagePath") or f"assets/projects/{project['id']}/source/cover.jpg")).is_file()
        and str(project["id"]) in artwork
        for project in projects
    )
    print(f"Generated high-resolution image-backed covers for {generated} projects; vector fallback retained for entries without collected artwork.")


if __name__ == "__main__":
    main()
