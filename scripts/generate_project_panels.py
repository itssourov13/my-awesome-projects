#!/usr/bin/env python3
"""Generate store-style project feature panels without pretending they are screenshots."""
from __future__ import annotations

import html
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PALETTES = {
    "Cybersecurity": ("#0a1419", "#183e42", "#d0ff70", "#72c9c7"),
    "AI & Developer Tools": ("#121229", "#38316e", "#c4a9ff", "#73dcff"),
    "Mobile Apps": ("#241b17", "#70452b", "#ffd079", "#f7a58b"),
    "Creative & 3D": ("#171822", "#43314e", "#e7adff", "#82d9e8"),
    "Web Apps": ("#141b2b", "#344a6a", "#c7e7ff", "#8aa7ff"),
    "Writing & Publishing": ("#28251f", "#605444", "#f0d6a3", "#c5cba8"),
    "Open Source": ("#14241b", "#28583c", "#c3f47c", "#89dcb3"),
    "Utilities": ("#171f2c", "#304e67", "#9fd6ff", "#b9f2b5"),
}


def escape(value: str) -> str:
    return html.escape(str(value or ""), quote=True)


def wrap(value: str, limit: int, max_lines: int = 3) -> list[str]:
    text = str(value or "").strip()
    lines = textwrap.wrap(text, width=limit, break_long_words=False, break_on_hyphens=False)
    if not lines:
        return [""]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .,:;") + "…"
    return lines


def text_lines(value: str, x: int, y: int, limit: int, size: int, color: str = "#f4f2eb",
               font: str = "system-ui,-apple-system,Segoe UI,sans-serif", weight: int = 500,
               line_height: int | None = None, max_lines: int = 3) -> str:
    lines = wrap(value, limit, max_lines)
    step = line_height or int(size * 1.35)
    return "".join(
        f'<text x="{x}" y="{y + index * step}" fill="{color}" font-family="{font}" font-size="{size}" font-weight="{weight}">{escape(line)}</text>'
        for index, line in enumerate(lines)
    )


def ui_mock(category: str, a1: str, a2: str, c1: str, c2: str, slide: int, project: dict) -> str:
    title = escape(project["title"])
    if category == "Mobile Apps":
        return f'''<g transform="translate(350 555)">
          <rect x="0" y="0" width="500" height="560" rx="38" fill="#080a0b" stroke="{a1}" stroke-opacity=".8" stroke-width="3"/>
          <rect x="18" y="18" width="464" height="524" rx="27" fill="{c1}"/>
          <rect x="186" y="28" width="128" height="9" rx="5" fill="#ffffff" fill-opacity=".2"/>
          <text x="48" y="92" fill="#ffffff" font-family="system-ui,sans-serif" font-size="22" font-weight="700">{title[:23]}</text>
          <rect x="44" y="117" width="412" height="108" rx="14" fill="{c2}"/>
          <circle cx="92" cy="161" r="22" fill="{a1}"/>
          <path d="M82 161 l7 7 l15 -16" stroke="{c1}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          <rect x="132" y="146" width="218" height="9" rx="4" fill="#ffffff" fill-opacity=".85"/>
          <rect x="132" y="166" width="150" height="7" rx="4" fill="#ffffff" fill-opacity=".35"/>
          <rect x="44" y="247" width="412" height="92" rx="12" fill="#ffffff" fill-opacity=".09"/>
          <rect x="64" y="268" width="200" height="8" rx="4" fill="#ffffff" fill-opacity=".7"/>
          <rect x="64" y="287" width="318" height="6" rx="3" fill="#ffffff" fill-opacity=".2"/>
          <rect x="64" y="303" width="256" height="6" rx="3" fill="#ffffff" fill-opacity=".2"/>
          <rect x="44" y="361" width="412" height="92" rx="12" fill="#ffffff" fill-opacity=".07"/>
          <rect x="64" y="382" width="175" height="8" rx="4" fill="#ffffff" fill-opacity=".7"/>
          <rect x="64" y="401" width="305" height="6" rx="3" fill="#ffffff" fill-opacity=".2"/>
          <rect x="44" y="472" width="412" height="44" rx="11" fill="{a1}"/>
          <text x="250" y="499" fill="{c1}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="13" font-weight="750">KEEP MOVING FORWARD</text>
        </g>'''
    if category == "Cybersecurity":
        rows = [
            ("[ OK ]", "Scope and input checks passed", a1),
            ("[ + ]", "Evidence collected locally", a2),
            ("[ !! ]", "Review findings and risk context", "#ffb77e"),
            ("[ -> ]", "Generate a structured report", a1),
        ]
        row_svg = ""
        for i, (mark, label, color) in enumerate(rows):
            y = 700 + i * 75
            row_svg += f'<text x="160" y="{y}" fill="{color}" font-family="monospace" font-size="20">{escape(mark)}</text><text x="260" y="{y}" fill="#e7ece6" font-family="monospace" font-size="17">{escape(label)}</text>'
        return f'''<g>
          <rect x="105" y="555" width="990" height="530" rx="22" fill="#080c0e" stroke="{a1}" stroke-opacity=".65" stroke-width="2"/>
          <path d="M105 610 H1095" stroke="#ffffff" stroke-opacity=".15"/>
          <circle cx="142" cy="582" r="7" fill="#ff897b"/><circle cx="166" cy="582" r="7" fill="#ffd079"/><circle cx="190" cy="582" r="7" fill="{a1}"/>
          <text x="225" y="589" fill="#9aa8a2" font-family="monospace" font-size="14">ASSESSMENT / LOCAL WORKSPACE</text>
          <text x="155" y="664" fill="{a1}" font-family="monospace" font-size="18">$ run --safe-mode</text>
          {row_svg}
        </g>'''
    if category == "Writing & Publishing":
        return f'''<g transform="translate(155 565)">
          <rect width="890" height="515" rx="14" fill="#dfd2b5"/>
          <rect x="24" y="24" width="842" height="467" rx="5" fill="#f3ead8" stroke="{c2}" stroke-opacity=".7"/>
          <text x="68" y="84" fill="{c1}" font-family="monospace" font-size="15" letter-spacing="3">NOTES / SELECTED PIECE</text>
          {text_lines(project["title"], 68, 158, 29, 42, c1, "Georgia,serif", 400, 54, 2)}
          <path d="M68 264 H785" stroke="{c2}" stroke-width="2"/>
          {''.join(f'<path d="M68 {310 + j * 30} H{780 - (j % 3) * 70}" stroke="{c2}" stroke-opacity=".8" stroke-width="4" stroke-linecap="round"/>' for j in range(5))}
          <circle cx="774" cy="425" r="35" fill="{a1}" fill-opacity=".7"/>
        </g>'''
    if category == "Creative & 3D":
        return f'''<g transform="translate(600 825)">
          <ellipse rx="340" ry="142" transform="rotate(-24)" fill="none" stroke="{a1}" stroke-width="3" stroke-opacity=".8"/>
          <ellipse rx="250" ry="350" transform="rotate(34)" fill="none" stroke="{a2}" stroke-width="3" stroke-opacity=".75"/>
          <ellipse rx="170" ry="275" transform="rotate(-44)" fill="none" stroke="#ffffff" stroke-width="2" stroke-opacity=".24"/>
          <circle r="154" fill="{c2}" fill-opacity=".35" stroke="{a1}" stroke-width="3"/>
          <circle r="95" fill="{c1}" stroke="{a2}" stroke-width="3"/>
          <circle cx="128" cy="-143" r="17" fill="{a1}"/><circle cx="-235" cy="103" r="12" fill="{a2}"/>
          <text x="0" y="12" fill="#ffffff" font-family="Georgia,serif" font-size="62" text-anchor="middle">{escape(project["title"][:13])}</text>
          <text x="0" y="48" fill="#e1dfeb" font-family="monospace" font-size="13" letter-spacing="3" text-anchor="middle">SPATIAL / MOTION / LIGHT</text>
        </g>'''
    if category == "AI & Developer Tools":
        return f'''<g>
          <rect x="85" y="555" width="1030" height="530" rx="18" fill="#10111b" stroke="{a1}" stroke-opacity=".75" stroke-width="2"/>
          <path d="M85 613 H1115" stroke="#ffffff" stroke-opacity=".14"/>
          <circle cx="122" cy="584" r="7" fill="#ff897b"/><circle cx="146" cy="584" r="7" fill="#ffd079"/><circle cx="170" cy="584" r="7" fill="{a1}"/>
          <text x="204" y="590" fill="#bbb7d6" font-family="monospace" font-size="14">WORKSPACE / ASSISTANT</text>
          <rect x="120" y="644" width="418" height="360" rx="12" fill="{c1}" stroke="{a1}" stroke-opacity=".38"/>
          <text x="150" y="687" fill="{a1}" font-family="monospace" font-size="14">01 / CONTEXT</text>
          {text_lines(project["description"], 150, 738, 38, 18, "#f0eff8", "system-ui,sans-serif", 500, 29, 5)}
          <rect x="150" y="920" width="350" height="48" rx="9" fill="{a1}"/>
          <text x="325" y="949" fill="#171523" text-anchor="middle" font-family="system-ui,sans-serif" font-size="14" font-weight="750">CONTINUE WORKFLOW</text>
          <rect x="565" y="644" width="515" height="360" rx="12" fill="#080a10" stroke="{a2}" stroke-opacity=".42"/>
          {''.join(f'<text x="600" y="{696 + j * 37}" fill="{a1 if j in (0,3,5) else "#a5acc0"}" font-family="monospace" font-size="16">{escape(line)}</text>' for j,line in enumerate(["// project context","const plan = await agent.plan();","await verify(plan);","// review changes","if (approved) deploy();","return { status: 'ready' };"]))}
        </g>'''
    return f'''<g>
      <rect x="95" y="555" width="1010" height="535" rx="22" fill="#0e121a" stroke="{a1}" stroke-opacity=".68" stroke-width="2"/>
      <path d="M95 614 H1105" stroke="#ffffff" stroke-opacity=".14"/>
      <circle cx="133" cy="585" r="7" fill="#ff897b"/><circle cx="157" cy="585" r="7" fill="#ffd079"/><circle cx="181" cy="585" r="7" fill="{a1}"/>
      <rect x="135" y="654" width="252" height="385" rx="13" fill="{c2}" fill-opacity=".62"/>
      <rect x="163" y="688" width="150" height="11" rx="5" fill="{a1}"/>
      <rect x="163" y="712" width="190" height="7" rx="3" fill="#ffffff" fill-opacity=".4"/>
      <rect x="163" y="730" width="166" height="7" rx="3" fill="#ffffff" fill-opacity=".25"/>
      <rect x="163" y="771" width="198" height="92" rx="9" fill="#ffffff" fill-opacity=".1"/>
      <path d="M182 835 L215 807 L245 820 L276 788 L334 805" fill="none" stroke="{a1}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
      <rect x="163" y="887" width="198" height="58" rx="8" fill="#ffffff" fill-opacity=".08"/>
      <rect x="184" y="908" width="128" height="7" rx="3" fill="#ffffff" fill-opacity=".7"/>
      <rect x="420" y="654" width="650" height="160" rx="13" fill="{c1}" stroke="{a1}" stroke-opacity=".33"/>
      {text_lines(project["title"], 454, 708, 30, 31, "#f4f2eb", "system-ui,sans-serif", 700, 40, 2)}
      {text_lines(project["description"], 454, 775, 74, 15, "#b8c6d4", "system-ui,sans-serif", 450, 25, 2)}
      <rect x="420" y="835" width="310" height="204" rx="13" fill="#ffffff" fill-opacity=".06"/>
      <rect x="753" y="835" width="317" height="204" rx="13" fill="#ffffff" fill-opacity=".04"/>
      <text x="448" y="879" fill="{a1}" font-family="monospace" font-size="13">01 / OVERVIEW</text>
      <path d="M448 910 H678 M448 929 H645 M448 948 H661 M448 967 H616" stroke="#ffffff" stroke-opacity=".28" stroke-width="5" stroke-linecap="round"/>
      <text x="782" y="879" fill="{a2}" font-family="monospace" font-size="13">02 / DETAILS</text>
      <rect x="782" y="900" width="253" height="53" rx="8" fill="{a2}" fill-opacity=".23"/>
      <rect x="782" y="968" width="253" height="47" rx="8" fill="{a1}" fill-opacity=".18"/>
    </g>'''


def panel_svg(project: dict, index: int, slide: int) -> str:
    category = project.get("category", "Web Apps")
    c1, c2, a1, a2 = PALETTES.get(category, PALETTES["Web Apps"])
    title = project.get("title", "Project")
    desc = project.get("description", "")
    highlights = project.get("highlights") or ["Project overview", "Key workflow", "Current status"]
    eyebrow = project.get("eyebrow") or category.upper()
    status = project.get("status", "Project index")
    stacks = project.get("stack") or []
    base = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600" viewBox="0 0 1200 1600" role="img" aria-labelledby="t d">
<title id="t">{escape(title)} — feature graphic {slide}</title>
<desc id="d">Original promotional composition for {escape(title)}. Not a live application screenshot.</desc>
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient><radialGradient id="glow"><stop stop-color="{a1}" stop-opacity=".28"/><stop offset="1" stop-color="{a1}" stop-opacity="0"/></radialGradient></defs>
<rect width="1200" height="1600" fill="url(#bg)"/>
<circle cx="1020" cy="240" r="460" fill="url(#glow)"/>
<g stroke="#ffffff" stroke-opacity=".07" stroke-width="1">{''.join(f'<path d="M0 {n} H1200"/>' for n in range(0,1601,50))}{''.join(f'<path d="M{n} 0 V1600"/>' for n in range(0,1201,50))}</g>
<rect x="80" y="78" width="10" height="10" rx="2" fill="{a1}"/>
<text x="110" y="90" fill="#ffffff" fill-opacity=".8" font-family="monospace" font-size="16" letter-spacing="3">{escape(eyebrow.upper())}</text>
<text x="80" y="145" fill="{a1}" font-family="monospace" font-size="12" letter-spacing="4">PROJECT VISUAL / {index:02d} / {slide:02d}</text>
'''
    if slide == 1:
        body = (
            text_lines(title, 80, 265, 25, 56, "#f5f4ef", "system-ui,-apple-system,Segoe UI,sans-serif", 750, 70, 3)
            + text_lines(desc, 82, 460, 59, 21, "#d4d8dc", "system-ui,-apple-system,Segoe UI,sans-serif", 450, 34, 3)
            + ui_mock(category, a1, a2, c1, c2, slide, project)
            + f'<text x="80" y="1215" fill="{a1}" font-family="monospace" font-size="14" letter-spacing="3">01 / THE OVERVIEW</text>'
            + text_lines("A closer look at the idea, the experience, and what the project is built to do.", 80, 1260, 59, 20, "#d4d8dc", "system-ui,sans-serif", 450, 32, 3)
        )
    elif slide == 2:
        body = (
            text_lines("What it brings together.", 80, 270, 23, 50, "#f5f4ef", "system-ui,sans-serif", 700, 65, 2)
            + text_lines("Key capabilities, workflows, and ideas that shape this build.", 82, 420, 56, 19, "#d4d8dc", "system-ui,sans-serif", 450, 32, 3)
        )
        for i, item in enumerate(highlights[:4]):
            y = 560 + i * 155
            body += f'<rect x="80" y="{y}" width="1040" height="126" rx="16" fill="#0a0d12" fill-opacity=".48" stroke="#ffffff" stroke-opacity=".13"/>'
            body += f'<text x="112" y="{y+43}" fill="{a1}" font-family="monospace" font-size="14">0{i+1:02d}</text>'
            body += text_lines(item, 188, y + 49, 43, 23, "#f4f2eb", "system-ui,sans-serif", 600, 31, 2)
            body += f'<path d="M1025 {y+31} l18 18 -18 18" stroke="{a1}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        body += f'<text x="80" y="1265" fill="{a1}" font-family="monospace" font-size="14" letter-spacing="3">DESIGNED AROUND THE WORKFLOW</text>'
        body += text_lines("A project-specific feature map, curated from the available repository notes.", 80, 1310, 60, 20, "#d4d8dc", "system-ui,sans-serif", 450, 32, 3)
    else:
        body = (
            text_lines("How it's put together.", 80, 270, 23, 50, "#f5f4ef", "system-ui,sans-serif", 700, 65, 2)
            + text_lines("A quick, public-safe snapshot of the tools and current state.", 82, 420, 57, 19, "#d4d8dc", "system-ui,sans-serif", 450, 32, 3)
        )
        body += '<rect x="80" y="555" width="1040" height="310" rx="18" fill="#090d11" fill-opacity=".58" stroke="#ffffff" stroke-opacity=".14"/>'
        body += f'<text x="120" y="610" fill="{a1}" font-family="monospace" font-size="14" letter-spacing="2">TECHNOLOGY / TOOLCHAIN</text>'
        for i, stack in enumerate(stacks[:6]):
            col = i % 2
            row = i // 2
            x = 120 + col * 490
            y = 665 + row * 65
            body += f'<rect x="{x}" y="{y}" width="440" height="45" rx="8" fill="#ffffff" fill-opacity=".07" stroke="#ffffff" stroke-opacity=".14"/>'
            body += f'<text x="{x+18}" y="{y+28}" fill="#f4f2eb" font-family="monospace" font-size="16">{escape(stack)}</text>'
            body += f'<circle cx="{x+410}" cy="{y+22}" r="5" fill="{a1}"/>'
        body += f'<rect x="80" y="915" width="1040" height="180" rx="18" fill="{c1}" stroke="{a1}" stroke-opacity=".6"/>'
        body += f'<text x="120" y="969" fill="{a1}" font-family="monospace" font-size="14" letter-spacing="2">CURRENT STATUS</text>'
        body += text_lines(status, 120, 1027, 37, 27, "#f4f2eb", "system-ui,sans-serif", 650, 35, 2)
        body += '<text x="80" y="1210" fill="#d4d8dc" font-family="system-ui,sans-serif" font-size="18">Source visibility and live preview access are listed separately.</text>'
        body += f'<text x="80" y="1265" fill="{a1}" font-family="monospace" font-size="14" letter-spacing="3">BUILD / TEST / REFINE</text>'
        body += text_lines("This graphic is a curated portfolio visual; it does not claim all listed features are production-ready.", 80, 1310, 59, 20, "#d4d8dc", "system-ui,sans-serif", 450, 32, 3)
    footer = f'''<path d="M80 1450 H1120" stroke="#ffffff" stroke-opacity=".24"/>
<text x="80" y="1490" fill="#ffffff" fill-opacity=".68" font-family="monospace" font-size="12" letter-spacing="2">MY AWESOME PROJECTS / SOUROV</text>
<text x="80" y="1530" fill="{a1}" font-family="monospace" font-size="11" letter-spacing="1.5">ORIGINAL PROMOTIONAL ART · NOT A LIVE SCREEN CAPTURE</text>
<text x="1118" y="1490" fill="#ffffff" fill-opacity=".6" font-family="monospace" font-size="12" text-anchor="end">{index:02d} / {slide:02d}</text>
</svg>'''
    return base + body + footer


def image_font(size: int, bold: bool = False):
    paths = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
        if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    )
    for path in paths:
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def image_wrap(draw, text: str, fnt, max_width: int, max_lines: int = 3) -> list[str]:
    words = textwrap.dedent(str(text or "")).strip().split()
    lines = []
    line = ""
    for word in words:
        candidate = (line + " " + word).strip()
        if not line or draw.textlength(candidate, font=fnt) <= max_width:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textlength(last + "...", font=fnt) > max_width:
            last = last[:-1].rstrip()
        lines[-1] = last + "..."
    return lines


def image_source_label(meta: dict) -> str:
    kind = meta.get("kind", "")
    if kind == "public-live-site-screenshot":
        return "LIVE SITE VISUAL"
    if kind == "project-page-open-graph":
        return "PROJECT SHARE ART"
    if kind == "public-repository-readme-image":
        return "REPOSITORY VISUAL"
    if kind == "public-web-reference":
        return "PUBLIC WEB REFERENCE"
    return "PROJECT VISUAL"


def raster_panel(project: dict, index: int, slide: int, source_path: Path, output: Path, meta: dict) -> None:
    category = project.get("category", "Web Apps")
    c1, c2, accent, accent2 = PALETTES.get(category, PALETTES["Web Apps"])
    with Image.open(source_path) as source:
        original = ImageOps.exif_transpose(source).convert("RGB")
        blurred = ImageOps.fit(original, (1200, 1600), method=Image.Resampling.LANCZOS, centering=(0.5, 0.38)).filter(ImageFilter.GaussianBlur(22))
        background = Image.new("RGB", (1200, 1600), c1)
        background = Image.blend(background, blurred, 0.36)
        image = background.convert("RGBA")
        hero = ImageOps.fit(original, (1200, 900), method=Image.Resampling.LANCZOS, centering=(0.52, 0.38)).convert("RGBA")
        overlay = Image.new("RGBA", hero.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay, "RGBA")
        for y in range(hero.height):
            alpha = int(45 + 135 * (y / max(1, hero.height - 1)))
            overlay_draw.line((0, y, hero.width - 1, y), fill=(6, 10, 16, alpha), width=1)
        hero = Image.alpha_composite(hero, overlay)
        image.alpha_composite(hero, (0, 0))
    fade = Image.new("RGBA", image.size, (0, 0, 0, 0))
    fade_draw = ImageDraw.Draw(fade, "RGBA")
    for y in range(620, 1600):
        strength = min(235, int(75 + 175 * ((y - 620) / 980)))
        fade_draw.line((0, y, 1199, y), fill=(7, 10, 15, strength), width=1)
    image = Image.alpha_composite(image, fade)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((70, 56, 81, 67), radius=3, fill=accent)
    draw.text((100, 52), str(project.get("eyebrow") or category).upper()[:44], font=image_font(14, True), fill=(247, 247, 241, 230))
    label = image_source_label(meta)
    label_font = image_font(10, True)
    label_width = int(draw.textlength(label, font=label_font)) + 28
    draw.rounded_rectangle((1130 - label_width, 45, 1130, 77), radius=15, fill=(6, 10, 15, 165), outline=(255, 255, 255, 60), width=1)
    draw.text((1144 - label_width, 55), label, font=label_font, fill=(247, 247, 241, 210))

    project_title = str(project.get("title") or "Project")
    if slide == 1:
        draw.text((74, 956), "THE PROJECT", font=image_font(14, True), fill=accent)
        title_fnt = image_font(46 if len(project_title) < 22 else 38, True)
        title_lines = image_wrap(draw, project_title, title_fnt, 1035, 2)
        cy = 1010
        for title_line in title_lines:
            draw.text((74, cy), title_line, font=title_fnt, fill=(250, 250, 246, 255))
            cy += title_fnt.size + 5
        desc = str(project.get("description") or "A project in the My Awesome Projects archive.")
        cy += 15
        for line in image_wrap(draw, desc, image_font(18), 1035, 4):
            draw.text((74, cy), line, font=image_font(18), fill=(231, 235, 236, 235))
            cy += 31
        draw.rounded_rectangle((74, 1328, 480, 1384), radius=14, fill=(7, 12, 18, 165), outline=(255, 255, 255, 65), width=1)
        draw.text((96, 1346), str(project.get("status") or "Project archive")[:38], font=image_font(16, True), fill=accent)
    elif slide == 2:
        draw.text((74, 830), "KEY HIGHLIGHTS", font=image_font(14, True), fill=accent)
        draw.text((74, 870), "What it brings together.", font=image_font(38, True), fill=(250, 250, 246, 255))
        highlights = project.get("highlights") if isinstance(project.get("highlights"), list) else []
        if not highlights:
            highlights = ["Project overview", "Core workflow", "Current direction"]
        cy = 950
        for i, item in enumerate(highlights[:4]):
            draw.rounded_rectangle((74, cy, 1126, cy + 82), radius=14, fill=(7, 11, 17, 192), outline=(255, 255, 255, 55), width=1)
            draw.rounded_rectangle((74, cy, 82, cy + 82), radius=4, fill=accent)
            draw.text((104, cy + 26), f"{i+1:02d}", font=image_font(14, True), fill=accent)
            text_lines = image_wrap(draw, str(item), image_font(20, True), 910, 2)
            ty = cy + (20 if len(text_lines) > 1 else 30)
            for line in text_lines:
                draw.text((164, ty), line, font=image_font(20, True), fill=(246, 246, 240, 245))
                ty += 27
            cy += 94
    else:
        draw.text((74, 830), "TECHNOLOGY / CURRENT STATE", font=image_font(14, True), fill=accent)
        draw.text((74, 870), "How it is put together.", font=image_font(38, True), fill=(250, 250, 246, 255))
        stack = project.get("stack") if isinstance(project.get("stack"), list) else []
        chip_x, chip_y = 74, 970
        for item in stack[:8]:
            label_text = str(item)[:25]
            fnt = image_font(16, True)
            chip_w = int(draw.textlength(label_text, font=fnt)) + 34
            if chip_x + chip_w > 1128:
                chip_x, chip_y = 74, chip_y + 60
            draw.rounded_rectangle((chip_x, chip_y, chip_x + chip_w, chip_y + 43), radius=13, fill=(7, 12, 18, 180), outline=(255, 255, 255, 60), width=1)
            draw.text((chip_x + 17, chip_y + 12), label_text, font=fnt, fill=(247, 247, 241, 238))
            chip_x += chip_w + 10
        draw.rounded_rectangle((74, 1195, 1126, 1338), radius=18, fill=(7, 12, 18, 188), outline=(255, 255, 255, 65), width=1)
        draw.text((104, 1225), "CURRENT STATUS", font=image_font(13, True), fill=accent)
        for idx, line in enumerate(image_wrap(draw, str(project.get("status") or "Project archive"), image_font(29, True), 960, 2)):
            draw.text((104, 1260 + idx * 38), line, font=image_font(29, True), fill=(250, 250, 246, 255))

    draw.line((74, 1460, 1126, 1460), fill=(255, 255, 255, 78), width=1)
    draw.text((74, 1490), "MY AWESOME PROJECTS  /  SOUROV", font=image_font(12, True), fill=(236, 240, 232, 180))
    draw.text((74, 1530), "PUBLIC WEB ARTWORK / CURATED PROJECT VISUAL", font=image_font(10, True), fill=(236, 240, 232, 135))
    draw.text((1125, 1490), f"{index:02d} / {slide:02d}", font=image_font(12, True), fill=accent, anchor="ra")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output, "WEBP", quality=88, method=6)


def main() -> None:
    catalog_path = ROOT / "projects.json"
    projects = json.loads(catalog_path.read_text(encoding="utf-8"))
    source_log_path = ROOT / "assets/artwork-sources.json"
    source_log = {}
    if source_log_path.exists():
        source_log = {item["id"]: item for item in json.loads(source_log_path.read_text(encoding="utf-8"))}
    total = 0
    for index, project in enumerate(projects, 1):
        original = project.get("screenshots") or []
        if original:
            project["gallery"] = original
            continue
        project_id = str(project["id"])
        metadata = source_log.get(project_id, {})
        source_rel = str(metadata.get("imagePath") or f"assets/projects/{project_id}/source/cover.jpg")
        source_part = Path(source_rel)
        if source_part.is_absolute() or ".." in source_part.parts:
            raise ValueError(f"Unsafe artwork source path for {project_id}: {source_rel}")
        source = ROOT / source_part
        output_dir = ROOT / "assets" / "projects" / project_id / "gallery"
        output_dir.mkdir(parents=True, exist_ok=True)
        gallery = []
        if source.is_file() and source_log.get(project_id, {}).get("status") != "failed":
            for slide in (1, 2, 3):
                rel = f"assets/projects/{project_id}/gallery/{slide:02d}-feature.webp"
                raster_panel(project, index, slide, source, ROOT / rel, source_log.get(project_id, {}))
                (ROOT / "assets" / "projects" / project_id / "gallery" / f"{slide:02d}-feature.svg").unlink(missing_ok=True)
                label = ["Overview visual", "Feature highlights", "Technology and status"][slide - 1]
                gallery.append({"src": rel, "alt": f"{project['title']} — {label} artwork panel"})
                total += 1
        else:
            for slide in (1, 2, 3):
                rel = f"assets/projects/{project_id}/gallery/{slide:02d}-feature.svg"
                (ROOT / rel).write_text(panel_svg(project, index, slide), encoding="utf-8")
                label = ["Overview visual", "Feature highlights", "Technology and status"][slide - 1]
                gallery.append({"src": rel, "alt": f"{project['title']} — {label} promotional graphic"})
                total += 1
        project["gallery"] = gallery
    catalog_path.write_text(json.dumps(projects, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {total} image-backed feature panels; retained supplied screenshot galleries where present.")


if __name__ == "__main__":
    main()
