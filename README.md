# My Awesome Projects

A visual, searchable index of projects by **Md Sourov Mondol / @itssourov13** — software products, security tooling, mobile experiments, writing, and immersive web experiences.

**This is a showcase, not a source-code mirror.** Public repository links are listed when appropriate. For projects whose code is not published, a curated entry can show approved details, screenshots, and a verified public live preview without linking to the private repository.

> **Current implementation status:** static gallery and project catalog are implemented. The catalog includes public repositories discovered during the inventory pass and a ScholarHub entry using the existing local promotional graphics. Some live preview URLs and private-project links are deliberately pending because a verified URL was not supplied or the current deployment failed verification.

## What's included

- Responsive project gallery with category filters, search, sorting, and featured projects.
- A detail view for each project with a summary, technical stack, highlights, status, and safe links.
- Local SVG cover art for the catalog entries; optional real screenshots and promotional graphics per project.
- A visual-gallery lightbox for locally hosted feature panels and supplied project graphics.
- Dark/light theme, keyboard-friendly controls, reduced-motion support, and semantic markup.
- No application framework, runtime API calls, database, analytics, external font dependency, or third-party UI package.
- A GitHub Actions workflow for publishing the static site to GitHub Pages.
- A validation script that checks the JSON catalog, local assets, link policy, and duplicate project IDs.

## Run locally

A local web server is recommended because the gallery fetches projects.json. From the repository root:

~~~bash
python3 -m http.server 4173
~~~

Open http://127.0.0.1:4173/.

No npm install is required. Validate the catalog and assets with:

~~~bash
python3 scripts/validate.py
node --check app.js
python3 -m json.tool projects.json > /dev/null
~~~

## Add or update a project

Edit projects.json. Each entry uses this general shape:

~~~json
{
  "id": "my-project",
  "title": "My Project",
  "eyebrow": "CATEGORY · SHORT LABEL",
  "category": "Web Apps",
  "description": "A concise, accurate summary of what the project does.",
  "story": "A little more context about the problem, decisions, or experiment.",
  "highlights": ["Feature one", "Feature two"],
  "stack": ["TypeScript", "React"],
  "sourceAccess": "hidden",
  "sourceUrl": "",
  "liveUrl": "https://example.com/",
  "demoLabel": "Live preview",
  "demoNote": "Any important access, demo, scope, or security caveat.",
  "status": "Live preview listed",
  "featured": false,
  "updated": "2026-10-25",
  "cover": "assets/projects/my-project/cover.svg",
  "gallery": [
    {
      "src": "assets/projects/my-project/screenshots/dashboard.png",
      "alt": "The project dashboard showing current tasks"
    }
  ]
}
~~~

### Source-link policy

- For a **public repository**, set sourceAccess to public and put the public source link in sourceUrl.
- For a **private or otherwise unpublished source**, set sourceAccess to hidden and leave sourceUrl empty. Do not put a private GitHub URL in any other public field.
- liveUrl is only for a confirmed HTTPS deployment that visitors are allowed to view. It is independent of source visibility.
- If a URL is private, login-gated, broken, or still needs access-control verification, do not label it as a public live preview.
- For intentionally vulnerable security labs, do not link to a public target until isolation, synthetic data, and access controls have been reviewed.
- Do not include secrets, production identifiers, private endpoints, customer data, or sensitive architecture in descriptions, images, metadata, or screenshots.

Read [docs/PRIVATE_PROJECTS.md](docs/PRIVATE_PROJECTS.md) before adding unpublished work.

## Image asset guidance

Every project has a locally hosted SVG cover plus three app-store-inspired visual panels. Generated panels summarize the project, features, and technology/status; they are original promotional artwork, **not** real application screenshots. ScholarHub also includes five existing PNG graphics from the workspace. Real UI captures may be added to each project's gallery when available and approved. See [docs/ASSET_GUIDELINES.md](docs/ASSET_GUIDELINES.md).

## Publish with GitHub Pages

1. Create a **public** GitHub repository named my-awesome-projects under the account you want to use for this showcase.
2. Push the default branch as main.
3. In **Settings → Pages**, select **GitHub Actions** as the publishing source.
4. Push to main; the pages.yml workflow validates the catalog and deploys the static files.
5. Wait for the Deploy to GitHub Pages workflow to finish. The published URL will be shown in the workflow summary and Pages settings.

GitHub's current guidance: [Deploying a website automatically](https://docs.github.com/en/get-started/start-your-journey/deploying-your-website-automatically) and [custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

### Push commands (after you create the GitHub repository)

~~~bash
cd /home/kali/gpt-workspace/my-awesome-projects
git remote add origin https://github.com/itssourov13/my-awesome-projects.git
git push -u origin main
~~~

If you create it in a different account, change the remote URL to match. The remote is intentionally not configured in this workspace yet; no repository was created or pushed automatically.

## Catalog status and known follow-ups

- The connected GitHub inventory returned 31 public repositories for itssourov13; the profile README currently reports 32 public repositories. Reconcile the count when the full account inventory is available.
- Private repositories were not enumerable through the current connected inventory. Add each private project only when its approved description and intended public live URL are known. Do not expose source links.
- ScholarHub's source is intentionally not linked. Its production preview at https://scholarhub-test.vercel.app/ was verified as reachable, and its existing promotional graphics are included in assets/projects/scholarhub/screenshots/.
- The hackerai-main repository homepage returned 404 during the audit. No live button is shown until a working deployment URL is confirmed.
- The public vulnerability lab's live link is intentionally withheld pending re-verification of deployment isolation.
- The claude-personal-website entry is labelled a concept/demo because the inspected page contained placeholder metrics and testimonial-style copy.

The full project inventory and confidence notes are maintained in [docs/PROJECT_CATALOG.md](docs/PROJECT_CATALOG.md).

## Project boundaries

This showcase is a static public site. **Anything committed here, including screenshots and text, must be considered public.** Making the portfolio repository private is not a substitute for deployment access controls on an individual app.

---

Curated for discovery. Source visibility and preview availability are handled separately.
