# Adding private-source projects safely

This repository is public. Anything committed here—including README content, projects.json, SVGs, images, commit history and docs—must be treated as public.

## Weekly manual workflow

Private projects are deliberately **not** enumerated by the automatic public-repository sync. Review them manually when a project is ready to be presented (for example, during a weekly showcase review).

1. Get or confirm the approved public title, summary, category, stack, highlights and current status. Do not copy internal notes wholesale.
2. Confirm the exact public HTTPS deployment URL, if one should be shown.
3. Open that URL in a signed-out/incognito browser. A login screen, deployment-protection page or access-denied response is not a public live preview.
4. Review the deployed app for private API routes, internal admin pages, credentials, debug output, real user/customer data and unsafe exposed endpoints.
5. For intentionally vulnerable labs, confirm isolation, synthetic data, explicit scope and suitable access controls. Keep the public live URL empty until that review is complete.
6. Add a manual entry to projects.json with sourceAccess set to hidden and sourceUrl set to an empty string. Add only approved public description/story/stack/highlights and graphics.
7. Set liveUrl only when anonymous access and deployment safety are verified. Source visibility and preview visibility are separate decisions.
8. Regenerate the README, covers, feature panels and catalog docs; run the test suite; then commit and push to main.

## Safe entry shape

~~~json
{
  "id": "private-dashboard",
  "title": "Private Dashboard",
  "eyebrow": "WEB APP · PRODUCT",
  "category": "Web Apps",
  "description": "An approved public summary of the project's purpose.",
  "story": "A public-safe case study; omit secrets and internal details.",
  "highlights": ["Key capability", "User-facing workflow"],
  "stack": ["TypeScript", "React"],
  "sourceAccess": "hidden",
  "sourceUrl": "",
  "liveUrl": "https://demo.example.com/",
  "demoLabel": "Live preview",
  "demoNote": "Public demo; private source is intentionally not linked.",
  "status": "Live preview listed",
  "featured": false,
  "updated": "2026-10-25",
  "cover": "assets/projects/private-dashboard/cover.svg",
  "screenshots": [],
  "gallery": []
}
~~~

The example domain is illustrative; never copy it as a real project URL.

## Never do these

- Never put a private GitHub URL in sourceUrl, descriptions, story, demoNote, image alt text, README content or button targets.
- Never put a private repository's URL/name in the public catalog just to support synchronization.
- Never mirror private source files or run the public sync with a personal token that can enumerate private repositories.
- Never put tokens, credentials, customer records, production identifiers, private endpoints or useful exploit artifacts in public files or screenshots.
- Never assume a private source repository means its deployment URL is private or secure.
- Never link an intentionally vulnerable application until isolation and deployment access controls have been reviewed.

The scheduled public sync uses only GitHub's public user-repository listing and applies an explicit public-only filter. It does not need access to private repositories. The README and web gallery use the same projects.json catalog; hidden sources remain unlinked in both.
