# Public artwork and project-visual guidelines

## Purpose

The showcase uses high-resolution public-web artwork as a visual starting point, then composes project-specific covers and feature panels locally. The aim is to make the gallery feel like a polished product index, instead of relying on placeholder geometric SVG artwork.

## Current asset system

- Each project has a locally hosted cover whose path is defined in projects.json. Image-backed projects use 1200 × 700 WebP covers with a project-aware color palette, title, category, status and stack.
- Three 1200 × 1600 WebP panels are generated for projects without a supplied screenshot gallery: project overview, key highlights, and technology/current status. They reuse the same high-resolution source image with different editorial layouts.
- Existing supplied ScholarHub PNG promotional graphics remain in assets/projects/scholarhub/screenshots/ and are used directly as its gallery. The showcase cover is restored from the historical pre-684bb55 cover; its visible BairePorbo wordmarks are replaced with ScholarHub, and the pristine historical WebP is retained beside the edited source for rollback.
- By default, source images are stored under assets/projects/<project-id>/source/cover.jpg. A deliberately supplied asset can use its own local path through imagePath in assets/artwork-sources.json; a custom coverOutput selects its generated cover path. This keeps owner-provided artwork reproducible and allows a new URL when an existing image path is cached.
- The asset collector prioritizes a project's public live-page sharing image, then an image from the public repository README, then a relevant public-web reference. It captures an ordinary public page only when a suitable image is unavailable.
- An external public reference is clearly labeled in the generated design; it is used as a visual reference, not presented as a screenshot of the project itself.
- The files are stored locally in the repository. The website does not need to fetch image assets from third-party hosts at runtime, which avoids extra runtime requests and hotlink dependency.

## Popular artwork copies

Popular has independent copies of selected covers/gallery visuals under `popular/public/<project-id>/assets/` or `popular/private/<project-id>/assets/`. Keep each project's paths local to its own folder. Do not make Popular depend on image paths in the main catalog; later catalog changes must not alter the curated section.

## Source and quality workflow

1. Run python3 scripts/collect_web_artwork.py to refresh public artwork sources. Use --only id1,id2 for a targeted refresh, or --missing to collect only missing source images. Entries marked user-provided-banner are preserved by the collector and are not silently replaced with page artwork.
2. Review assets/artwork-sources.json alongside the downloaded images.
3. Run python3 scripts/generate_covers.py and python3 scripts/generate_project_panels.py to create optimized WebP output.
4. Run python3 scripts/generate_readme.py and python3 scripts/generate_catalog.py so the README and catalog docs point at the new paths.
5. Run python3 scripts/validate.py and python3 -m unittest discover -s tests -v before committing.

For manually added private-source projects, only public, approved descriptions and graphics belong here. A private source URL must remain empty. Do not add internal dashboard captures, credentials, customer data, private endpoints or unreleased details. A live preview is separate from source visibility and should be added only after confirming signed-out access and public safety.

## Fallback behavior

New public repositories may not have an immediately suitable public image. The collector tries their public live URL and public repository README before using available project-specific mappings. If it cannot collect an image, the generator retains a local vector fallback; that one entry does not block the rest of the showcase deployment.

## Regenerate

~~~bash
python3 scripts/collect_web_artwork.py --missing
python3 scripts/generate_covers.py
python3 scripts/generate_project_panels.py
python3 scripts/generate_readme.py
python3 scripts/generate_catalog.py
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
~~~
