#!/usr/bin/env python3
"""Generate store-style project feature panels without pretending they are screenshots."""
from __future__ import annotations

import html
import json
import textwrap
from pathlib import Path

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


def main() -> None:
    catalog_path = ROOT / "projects.json"
    projects = json.loads(catalog_path.read_text(encoding="utf-8"))
    total = 0
    for index, project in enumerate(projects, 1):
        original = project.get("screenshots") or []
        if original:
            project["gallery"] = original
            continue
        project_id = project["id"]
        output_dir = ROOT / "assets" / "projects" / project_id / "gallery"
        output_dir.mkdir(parents=True, exist_ok=True)
        gallery = []
        for slide in (1, 2, 3):
            rel = f"assets/projects/{project_id}/gallery/{slide:02d}-feature.svg"
            (ROOT / rel).write_text(panel_svg(project, index, slide), encoding="utf-8")
            label = ["Overview visual", "Feature highlights", "Technology and status"][slide-1]
            gallery.append({"src": rel, "alt": f"{project['title']} — {label} promotional graphic"})
            total += 1
        project["gallery"] = gallery
    catalog_path.write_text(json.dumps(projects, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {total} feature panels and populated gallery entries for {len(projects)} projects.")


if __name__ == "__main__":
    main()
