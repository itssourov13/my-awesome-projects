#!/usr/bin/env python3
"""Generate original SVG cover artwork for every catalog entry."""
from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path

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
CATEGORY_MARK = {
    "Cybersecurity": "SECURITY / TOOLING",
    "AI & Developer Tools": "AI / ENGINEERING",
    "Mobile Apps": "MOBILE / PRODUCT",
    "Creative & 3D": "CREATIVE COMPUTING",
    "Web Apps": "WEB / PRODUCT",
    "Writing & Publishing": "WRITING / EDITORIAL",
    "Open Source": "OPEN SOURCE",
    "Utilities": "UTILITY / EXPERIMENT",
}


def split_title(title: str, max_len: int = 19) -> list[str]:
    words = title.split()
    lines: list[str] = []
    line = ""
    for word in words:
        if len(line) + len(word) + (1 if line else 0) <= max_len:
            line = f"{line} {word}".strip()
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    if len(lines) > 3:
        lines = lines[:2] + [" ".join(lines[2:])[:max_len - 1] + "…"]
    return lines or ["PROJECT"]


def visual(category: str, c1: str, c2: str, a1: str, a2: str, idx: int) -> str:
    if category == "Mobile Apps":
        return f"""
        <g transform="translate(755 98) rotate(7 120 240)">
          <rect x="0" y="0" width="228" height="440" rx="28" fill="#0b0c0f" stroke="{a1}" stroke-opacity=".82" stroke-width="2"/>
          <rect x="12" y="14" width="204" height="412" rx="19" fill="{c1}" stroke="#ffffff" stroke-opacity=".14"/>
          <rect x="78" y="22" width="72" height="7" rx="4" fill="#ffffff" fill-opacity=".18"/>
          <rect x="28" y="56" width="112" height="8" rx="4" fill="{a1}" fill-opacity=".9"/>
          <rect x="28" y="75" width="158" height="22" rx="5" fill="#ffffff" fill-opacity=".10"/>
          <rect x="28" y="111" width="172" height="82" rx="9" fill="{c2}" fill-opacity=".56"/>
          <circle cx="61" cy="144" r="18" fill="{a1}" fill-opacity=".95"/>
          <rect x="89" y="132" width="78" height="6" rx="3" fill="#ffffff" fill-opacity=".9"/>
          <rect x="89" y="147" width="58" height="5" rx="3" fill="#ffffff" fill-opacity=".44"/>
          <rect x="28" y="208" width="172" height="50" rx="8" fill="#ffffff" fill-opacity=".09"/>
          <rect x="40" y="222" width="83" height="6" rx="3" fill="#ffffff" fill-opacity=".65"/>
          <rect x="40" y="236" width="130" height="5" rx="2.5" fill="#ffffff" fill-opacity=".22"/>
          <rect x="28" y="271" width="172" height="50" rx="8" fill="#ffffff" fill-opacity=".08"/>
          <rect x="40" y="285" width="73" height="6" rx="3" fill="#ffffff" fill-opacity=".65"/>
          <rect x="40" y="299" width="118" height="5" rx="2.5" fill="#ffffff" fill-opacity=".22"/>
          <rect x="28" y="338" width="172" height="34" rx="8" fill="{a1}"/>
          <rect x="72" y="352" width="84" height="6" rx="3" fill="{c1}"/>
        </g>"""
    if category == "Cybersecurity":
        return f"""
        <g transform="translate(720 144)">
          <circle cx="138" cy="154" r="145" stroke="{a1}" stroke-opacity=".24" fill="none"/>
          <circle cx="138" cy="154" r="108" stroke="{a1}" stroke-opacity=".35" fill="none" stroke-dasharray="4 8"/>
          <circle cx="138" cy="154" r="70" stroke="{a2}" stroke-opacity=".55" fill="{c1}" fill-opacity=".45"/>
          <path d="M138 16 L138 56 M138 252 L138 292 M0 154 L38 154 M238 154 L276 154" stroke="{a1}" stroke-opacity=".7"/>
          <rect x="68" y="84" width="140" height="140" rx="18" fill="#0b1214" stroke="{a1}" stroke-opacity=".7"/>
          <path d="M92 123 L112 141 L92 159 M122 162 H166" fill="none" stroke="{a1}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="226" cy="48" r="7" fill="{a2}"/><circle cx="48" cy="245" r="5" fill="{a1}"/>
          <path d="M218 57 L195 83 M55 238 L74 216" stroke="{a2}" stroke-opacity=".55" stroke-width="1.5"/>
        </g>
        <g transform="translate(710 477)" fill="{a1}" font-family="monospace" font-size="10" opacity=".8">
          <text x="0" y="0">SCOPE / EVIDENCE / VERIFY</text>
          <text x="0" y="17" fill="{a2}">[ LOCAL · AUDIT · REPORT ]</text>
        </g>"""
    if category == "Creative & 3D":
        return f"""
        <g transform="translate(775 125)">
          <ellipse cx="105" cy="175" rx="92" ry="170" fill="none" stroke="{a1}" stroke-width="1.5" stroke-opacity=".72" transform="rotate(31 105 175)"/>
          <ellipse cx="105" cy="175" rx="92" ry="170" fill="none" stroke="{a2}" stroke-width="1.5" stroke-opacity=".65" transform="rotate(-31 105 175)"/>
          <ellipse cx="105" cy="175" rx="155" ry="78" fill="none" stroke="#ffffff" stroke-opacity=".25" transform="rotate(-21 105 175)"/>
          <circle cx="105" cy="175" r="72" fill="{c2}" fill-opacity=".28"/>
          <circle cx="105" cy="175" r="58" fill="url(#orb)" stroke="{a1}" stroke-opacity=".85"/>
          <circle cx="105" cy="175" r="31" fill="{c1}" stroke="{a2}" stroke-opacity=".8"/>
          <circle cx="158" cy="81" r="7" fill="{a1}"/><circle cx="10" cy="252" r="6" fill="{a2}"/>
          <path d="M25 100 L54 129 M165 231 L190 263" stroke="#ffffff" stroke-opacity=".32"/>
        </g>"""
    if category == "AI & Developer Tools":
        return f"""
        <g transform="translate(746 138)" fill="none">
          <path d="M52 45 L174 97 L100 220 L218 290 M174 97 L266 42 M100 220 L38 300 M174 97 L224 180" stroke="{a2}" stroke-opacity=".52" stroke-width="2"/>
          <circle cx="52" cy="45" r="22" fill="{c1}" stroke="{a1}" stroke-width="2"/>
          <circle cx="174" cy="97" r="35" fill="{c2}" stroke="{a1}" stroke-width="2"/>
          <circle cx="100" cy="220" r="28" fill="{c1}" stroke="{a2}" stroke-width="2"/>
          <circle cx="218" cy="290" r="19" fill="{c2}" stroke="{a1}" stroke-width="2"/>
          <circle cx="266" cy="42" r="17" fill="{c1}" stroke="{a2}" stroke-width="2"/>
          <circle cx="38" cy="300" r="16" fill="{c2}" stroke="{a1}" stroke-width="2"/>
          <circle cx="224" cy="180" r="11" fill="{a1}"/>
          <path d="M44 45h16 M52 37v16 M163 97h22 M174 86v22 M92 220h16 M100 212v16" stroke="{a1}" stroke-width="2"/>
        </g>"""
    if category == "Writing & Publishing":
        return f"""
        <g transform="translate(740 128) rotate(3 135 190)">
          <rect x="0" y="0" width="258" height="360" rx="7" fill="#e5d6b8" fill-opacity=".96"/>
          <rect x="18" y="18" width="222" height="324" rx="3" fill="none" stroke="{c2}" stroke-opacity=".65"/>
          <text x="32" y="61" fill="{c1}" font-family="Georgia,serif" font-size="12" letter-spacing="3">FIELD NOTES</text>
          <path d="M32 89 H222" stroke="{c2}" stroke-width="1"/>
          <text x="32" y="137" fill="{c1}" font-family="Georgia,serif" font-size="26">Words,</text>
          <text x="32" y="168" fill="{c1}" font-family="Georgia,serif" font-size="26" font-style="italic">worth keeping.</text>
          <path d="M32 201 H208 M32 216 H214 M32 231 H188 M32 246 H216 M32 261 H180" stroke="{c2}" stroke-width="3" stroke-linecap="round" stroke-opacity=".8"/>
          <circle cx="198" cy="296" r="17" fill="{a1}" fill-opacity=".7"/>
        </g>"""
    if category == "Open Source":
        return f"""
        <g transform="translate(750 150)">
          <rect x="0" y="0" width="260" height="255" rx="12" fill="{c1}" stroke="{a1}" stroke-opacity=".62"/>
          <rect x="0" y="0" width="260" height="38" rx="12" fill="#ffffff" fill-opacity=".07"/>
          <circle cx="19" cy="19" r="4" fill="{a1}"/><circle cx="34" cy="19" r="4" fill="{a2}"/><circle cx="49" cy="19" r="4" fill="#ffffff" fill-opacity=".35"/>
          <path d="M22 70 H171 M22 91 H213 M22 112 H130 M22 145 H198 M22 166 H151 M22 187 H220" stroke="#ffffff" stroke-opacity=".34" stroke-width="6" stroke-linecap="round"/>
          <rect x="173" y="218" width="65" height="20" rx="5" fill="{a1}" fill-opacity=".8"/>
          <path d="M45 280 L82 317 L45 354 M104 354 H172" stroke="{a1}" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </g>"""
    # A browser/product canvas for Web Apps and Utilities.
    return f"""
    <g transform="translate(724 142)">
      <rect x="0" y="0" width="294" height="244" rx="12" fill="{c1}" stroke="{a1}" stroke-opacity=".68" stroke-width="1.4"/>
      <path d="M0 36 H294" stroke="#ffffff" stroke-opacity=".15"/>
      <circle cx="18" cy="18" r="4" fill="{a1}"/><circle cx="33" cy="18" r="4" fill="{a2}"/><circle cx="48" cy="18" r="4" fill="#ffffff" fill-opacity=".3"/>
      <rect x="19" y="58" width="114" height="12" rx="4" fill="{a1}" fill-opacity=".85"/>
      <rect x="19" y="80" width="172" height="6" rx="3" fill="#ffffff" fill-opacity=".36"/>
      <rect x="19" y="94" width="143" height="6" rx="3" fill="#ffffff" fill-opacity=".2"/>
      <rect x="19" y="121" width="116" height="78" rx="7" fill="{c2}" fill-opacity=".64"/>
      <rect x="147" y="121" width="128" height="34" rx="7" fill="#ffffff" fill-opacity=".1"/>
      <rect x="147" y="165" width="128" height="34" rx="7" fill="#ffffff" fill-opacity=".07"/>
      <path d="M28 180 L47 164 L63 172 L86 143 L115 157" fill="none" stroke="{a1}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
      <rect x="19" y="213" width="256" height="13" rx="5" fill="#ffffff" fill-opacity=".08"/>
    </g>"""


def cover_svg(project: dict, index: int) -> str:
    category = project.get("category", "Web Apps")
    c1, c2, a1, a2 = PALETTES.get(category, PALETTES["Web Apps"])
    title_lines = split_title(project.get("title", "Project"))
    title_svg = []
    y = 328
    for i, line in enumerate(title_lines):
        title_svg.append(
            f'<text x="70" y="{y + i * 61}" fill="#f5f4ed" font-family="system-ui,-apple-system,Segoe UI,sans-serif" font-weight="680" font-size="48" letter-spacing="-2.2">{html.escape(line)}</text>'
        )
    eyebrow = html.escape(project.get("eyebrow") or CATEGORY_MARK.get(category, "PROJECT INDEX"))
    category_label = html.escape(category.upper())
    short_id = f"{index:02d}"
    visual_svg = visual(category, c1, c2, a1, a2, index)
    description = html.escape(project.get("description", "")[:130])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(project.get("title", "Project"))} — project cover</title>
<desc id="desc">{description}</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
  <linearGradient id="orb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a1}" stop-opacity=".92"/><stop offset="1" stop-color="{a2}" stop-opacity=".2"/></linearGradient>
  <radialGradient id="glow"><stop stop-color="{a1}" stop-opacity=".26"/><stop offset="1" stop-color="{a1}" stop-opacity="0"/></radialGradient>
</defs>
<rect width="1200" height="700" fill="url(#bg)"/>
<circle cx="1080" cy="78" r="360" fill="url(#glow)"/>
<circle cx="105" cy="620" r="315" fill="{a2}" opacity=".055"/>
<g opacity=".12" stroke="#ffffff" stroke-width="1">
  {''.join(f'<path d="M{n} 0 V700"/>' for n in range(0,1201,40))}
  {''.join(f'<path d="M0 {n} H1200"/>' for n in range(0,701,40))}
</g>
<path d="M70 70 H535" stroke="{a1}" stroke-width="2" stroke-opacity=".82"/>
<rect x="70" y="57" width="8" height="8" rx="2" fill="{a1}"/>
<text x="92" y="65" fill="#ffffff" fill-opacity=".72" font-family="monospace" font-size="13" letter-spacing="2.3">{eyebrow}</text>
<text x="70" y="238" fill="{a1}" font-family="monospace" font-size="12" letter-spacing="3.1">{category_label}</text>
{''.join(title_svg)}
<path d="M70 525 H525" stroke="#ffffff" stroke-opacity=".25"/>
<text x="70" y="557" fill="#ffffff" fill-opacity=".74" font-family="system-ui,sans-serif" font-size="15">{html.escape(project.get("status", "Project index"))}</text>
<text x="70" y="624" fill="#ffffff" fill-opacity=".39" font-family="monospace" font-size="10" letter-spacing="2.3">MY AWESOME PROJECTS / SOUROV</text>
<text x="70" y="656" fill="{a1}" font-family="monospace" font-size="11" letter-spacing="1.5">SHOW THE WORK · RESPECT THE BOUNDARIES</text>
{visual_svg}
<g transform="translate(1080 640)">
  <rect x="-45" y="-28" width="90" height="56" rx="8" fill="#08090b" fill-opacity=".24" stroke="#ffffff" stroke-opacity=".18"/>
  <text x="0" y="8" fill="#ffffff" fill-opacity=".9" font-family="monospace" font-size="19" text-anchor="middle">{short_id}</text>
</g>
</svg>'''


def main() -> None:
    projects = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
    for index, project in enumerate(projects, 1):
        target = ROOT / project["cover"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(cover_svg(project, index), encoding="utf-8")

    brand = ROOT / "assets/brand"
    brand.mkdir(parents=True, exist_ok=True)
    (brand / "favicon.svg").write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="15" fill="#101114"/><rect x="13" y="34" width="9" height="16" rx="3" fill="#c6f56c" opacity=".65"/><rect x="27" y="16" width="9" height="34" rx="3" fill="#c6f56c"/><rect x="41" y="25" width="9" height="25" rx="3" fill="#c6f56c" opacity=".8"/></svg>''', encoding="utf-8")
    (brand / "og-cover.svg").write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630"><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#101114"/><stop offset="1" stop-color="#26362b"/></linearGradient><radialGradient id="glow"><stop stop-color="#c6f56c" stop-opacity=".3"/><stop offset="1" stop-color="#c6f56c" stop-opacity="0"/></radialGradient></defs><rect width="1200" height="630" fill="url(#bg)"/><circle cx="1000" cy="210" r="360" fill="url(#glow)"/><g stroke="#ffffff" stroke-opacity=".07"><path d="M0 70H1200M0 140H1200M0 210H1200M0 280H1200M0 350H1200M0 420H1200M0 490H1200M0 560H1200"/><path d="M70 0V630M140 0V630M210 0V630M280 0V630M350 0V630M420 0V630M490 0V630M560 0V630M630 0V630M700 0V630M770 0V630M840 0V630M910 0V630M980 0V630M1050 0V630M1120 0V630"/></g><rect x="78" y="85" width="9" height="9" rx="2" fill="#c6f56c"/><text x="103" y="96" fill="#c6f56c" font-family="monospace" font-size="15" letter-spacing="4">THE WORK INDEX / 2026</text><text x="78" y="260" fill="#f2f0e9" font-family="system-ui,sans-serif" font-size="70" font-weight="700" letter-spacing="-4">MY AWESOME</text><text x="78" y="344" fill="#c6f56c" font-family="Georgia,serif" font-size="82" font-style="italic">PROJECTS.</text><text x="82" y="410" fill="#c6c9c1" font-family="system-ui,sans-serif" font-size="21">Built to solve. Made to explore.</text><text x="82" y="550" fill="#a8afa2" font-family="monospace" font-size="12" letter-spacing="2">CYBERSECURITY · ENGINEERING · CREATIVE COMPUTING</text><circle cx="930" cy="320" r="150" stroke="#c6f56c" stroke-opacity=".4" fill="none"/><ellipse cx="930" cy="320" rx="210" ry="90" transform="rotate(-32 930 320)" stroke="#b7a2ff" stroke-opacity=".7" fill="none"/><ellipse cx="930" cy="320" rx="95" ry="210" transform="rotate(34 930 320)" stroke="#c6f56c" stroke-opacity=".5" fill="none"/><circle cx="930" cy="320" r="60" fill="#c6f56c" fill-opacity=".16" stroke="#c6f56c" stroke-opacity=".8"/><text x="930" y="342" fill="#c6f56c" font-family="Georgia,serif" font-size="66" text-anchor="middle">∞</text></svg>''', encoding="utf-8")
    print(f"Generated {len(projects)} project covers and 2 brand assets.")


if __name__ == "__main__":
    main()
