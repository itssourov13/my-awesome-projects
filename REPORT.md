# Implementation report — My Awesome Projects

**Date:** 25 October 2026
**Workspace:** /home/kali/gpt-workspace/my-awesome-projects
**Branch:** feat/readme-first-public-sync
**Remote:** https://github.com/itssourov13/my-awesome-projects.git
**Publication status:** implementation is local and not pushed or merged; the existing live site remains on the current main branch until this branch is merged.

## Scope implemented

The repository README is now the primary project showcase. The existing static website remains the companion interactive gallery. The profile/special repository and other project repositories were not changed.

- Replaced the documentation-first README with a visual catalogue: hero artwork, project-count summary, six featured project cards, category-grouped cards for the rest of the catalog, project covers, curated descriptions, stack/status details, and independently rendered source/live links.
- Added scripts/generate_readme.py. The README is deterministic output from projects.json and supports --check.
- Added scripts/sync_public_projects.py. It fetches the complete public-repository inventory for itssourov13 before changing the catalog; adds new public repositories, updates last-push metadata, and refreshes metadata only for entries explicitly managed as GitHub-generated.
- Public metadata sync fails closed: repositories absent from the verified public inventory lose their public source link. Private/manual entries are not enumerated and are not rewritten by the public sync.
- Added a scheduled GitHub Actions publication workflow that runs every six hours, refreshes public metadata, regenerates covers/panels/README/catalog docs, validates output, commits generated changes only when necessary, then deploys GitHub Pages in the same run.
- Added a separate pull-request README consistency check; regular main-branch catalog pushes are allowed to regenerate the README automatically.
- Updated private-project documentation for the agreed weekly manual process. Only approved metadata, approved graphics, and a separately verified public HTTPS preview should be committed. Private source URLs remain empty.
- Replaced stale hand-written inventory notes with a generated catalog report based on projects.json.
- Added unit tests for public-only inventory filtering, newly discovered repositories, preservation of curated metadata, fail-closed handling when a repository is no longer public, duplicate suppression for a manually hidden project, and README privacy behavior.

## Current catalog after the public-inventory check

- 32 project entries across 8 categories.
- 31 public source entries and 1 source-hidden entry (ScholarHub).
- 14 public preview URLs.
- 98 gallery visuals (the existing five ScholarHub graphics plus generated panels).
- The public GitHub API returned 31 owned public repositories before the showcase repository was excluded; the catalog reconciled to those public sources without adding duplicate entries.
- The ScholarHub source entry remains intentionally hidden. Its public preview remains listed independently.

## Verification results

**Passed locally**
- Python compile checks for all scripts/tests.
- projects.json parses as valid JSON.
- scripts/validate.py: 32 entries, 8 categories, 31 public source entries, 1 hidden source, 14 HTTPS preview URLs, no errors or warnings.
- scripts/generate_readme.py --check: generated README matches the current catalog.
- node --check app.js.
- Unit tests: 18 passed.
- The public sync was run against GitHub's public repository inventory. The script's unit tests also exercise private-record filtering without network access.
- Public data sync, generated artwork, README output, and catalog documentation are all represented on this feature branch.

## Deployment and owner follow-up

The GitHub Pages deployment and scheduled sync workflow changes are **not live yet**, because this feature branch has not been pushed/merged. After the branch is pushed and merged to main:

1. The push to main triggers the Sync public projects and deploy showcase workflow.
2. It will refresh public project metadata, generate the README/artwork, validate everything, commit any generated differences, and deploy the static site.
3. The same scheduled workflow then repeats every six hours. Private/unpublished projects remain manual weekly edits to projects.json; no private-source token or special-repository modification is required.

## Security boundaries

- The workflow uses the repository-scoped GITHUB_TOKEN and calls only the public user-repository API. It does not use a personal token or request private repositories.
- Catalog entries marked sourceAccess = hidden must have an empty sourceUrl and cannot carry the githubRepo internal identifier.
- Live preview visibility is separate from source visibility. The sync never guesses a live deployment URL for a newly discovered repository.
- Deliberately vulnerable labs remain without a public preview until isolation and deployment access controls are verified.
- The user must still review new public-repository entries for copy quality, categories, and any live preview before manually adding those details.
