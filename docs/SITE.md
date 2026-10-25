# Website guide

The showcase site is a dependency-free static page (`index.html`, `styles.css`, `app.js`) that renders `projects.json` in the browser. The README and `docs/PROJECT_CATALOG.md` are generated from the same catalog, so all three stay consistent.

## Files

| File | Role |
|---|---|
| `index.html` | Page structure: header, hero, selected work, filterable index, about note, footer, dialogs |
| `styles.css` | Design tokens (dark and light themes), layout, components, responsive rules |
| `app.js` | Loads `projects.json`, renders cards, filters, URL state, dialogs, footer data |
| `projects.json` | Single source of truth for every entry |
| `scripts/generate_readme.py` | README showcase (uses the same category order and featured limit as the site) |
| `scripts/generate_catalog.py` | `docs/PROJECT_CATALOG.md`, including the technology index |
| `scripts/validate.py`, `tests/` | Catalog, link-policy and site-contract checks |

## Discovery features

- **Search** matches title, eyebrow, category, description, story, status, stack and highlights. Every word must match; title matches rank first. Press `/` to focus the search box and `Esc` to clear it.
- **Discipline** chips filter by category. Categories use the same order as the README.
- **Show only** toggles: Featured, Live preview, Public source.
- **Technologies** panel filters by stack tag and requires all selected technologies to match. It lists technologies used by two or more projects; version suffixes such as `3.11+` are ignored (matching the technology index in the catalog notes). Search covers the rest.
- **Sort**: Featured first, Best match, Recently updated, Live previews first, Name A–Z. "Best match" is selected automatically while searching until you pick a sort yourself.
- Chip counts show how many results selecting or deselecting that specific chip would produce while keeping all other filters unchanged; chips that would give none are dimmed.
- Project dialogs include an image viewer (cover plus gallery, keyboard and swipe support), clickable technology tags that filter the index, related projects, and a copy-link button. When related-project navigation replaces an open dialog, focus returns to its stable close control rather than a removed element.

### URL parameters

State is mirrored into the query string with `history.replaceState`, so filtered views and open projects can be shared.

| Parameter | Example | Meaning |
|---|---|---|
| `q` | `?q=three.js` | Search text |
| `cat` | `?cat=Cybersecurity` | Category |
| `tech` | `?tech=python,cli` | Technology keys (lower case, comma separated, all must match) |
| `f` | `?f=live,public` | Quick filters: `featured`, `live`, `public` |
| `sort` | `?sort=recent` | Only present after an explicit sort choice |
| `project` | `?project=scholarhub` | Opens that project's dialog |

Unknown values are ignored.

## Footer

The footer is static HTML with two data-driven parts filled by `app.js`: the category links (with counts, using the same filters as the index) and the stats line (projects, live previews, public sources, latest catalog update). Static links go only to the public GitHub profile, this repository and its public docs. The `tests/test_site.py` suite fails if the footer loses its navigation, profile link or copyright, or if any static GitHub link points elsewhere.

## Source and preview link rules (unchanged)

- A source link is rendered only when `sourceAccess` is `public` **and** `sourceUrl` is an HTTPS `github.com` URL (`sourceUrlOf` and `isGithubUrl` in `app.js`).
- Hidden-source entries show a "Source hidden" pill and no source link. `githubRepo` is never rendered, and hidden entries' identifiers must not appear in any site file (enforced by tests).
- Live preview links are independent of source visibility and require an HTTPS `liveUrl`.
- Image paths must be local relative paths; anything else is ignored.

## Design system

Tokens live at the top of `styles.css` (`--bg`, `--panel`, `--accent`, `--line`, `--radius`, `--shadow`, type stacks). Light mode overrides them under `:root[data-theme="light"]`; the saved choice is stored in `localStorage` under `awesome-projects-theme` and applied by a small inline script in `<head>` before first paint. Fonts are system stacks so the site stays self-contained. Motion respects `prefers-reduced-motion`.

## Changing the site

1. Edit `projects.json` for content; edit `index.html`, `styles.css` or `app.js` for presentation.
2. If you add a category, add it to `CATEGORY_ORDER` in both `app.js` and `scripts/generate_readme.py` (a test keeps them aligned).
3. If you add an element that `app.js` looks up with `$("#id")`, add the matching `id` to `index.html` (a test checks this).
4. Regenerate and verify:

~~~bash
python3 scripts/generate_readme.py
python3 scripts/generate_catalog.py
python3 -m json.tool projects.json > /dev/null
python3 scripts/validate.py
python3 scripts/generate_readme.py --check
node --check app.js
python3 -m unittest discover -s tests -v
~~~

To preview locally, serve the folder (the catalog is loaded with `fetch`, which `file://` blocks): `python3 -m http.server 8000`.

## Responsive layout

The project grids use three columns on wide screens, two columns on tablet-sized screens, and one column on mobile. The hero showcase covers retain their landscape 1200:700 ratio at every breakpoint; their intrinsic HTML dimensions must not force a fixed rendered height. The decorative hero backdrop stays inside the hero so it cannot expand the page viewport. Mobile page margins, card gaps, and the compact header are adjusted at the smaller breakpoints.
