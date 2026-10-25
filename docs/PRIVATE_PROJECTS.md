# Adding private-source projects safely

The portfolio should show what a project does without disclosing its source repository. The source-visibility setting and live-deployment URL are independent.

## Publicly showing an unpublished project

1. Confirm the project owner approves publishing the name, summary, screenshots, technical stack, and any case-study details.
2. Confirm the exact live URL the visitor is allowed to open. Do not infer it from a private repository name or guess a Vercel hostname.
3. Open the URL in a signed-out/incognito session and confirm whether it is intended for anonymous visitors. A login screen, deployment-protection page, or access-denied response is not a public live preview.
4. Review the deployment for credentials, private API routes, internal admin pages, private customer/user data, and unsafe debug output.
5. If the app is intentionally vulnerable, treat it as a security lab: synthetic data only, isolated services and credentials, explicit scope, and access controls appropriate to the risk. Withhold the public preview link until that review passes.
6. Add the project to projects.json with sourceAccess set to "hidden", sourceUrl set to an empty string, and liveUrl set only to the verified public HTTPS URL.
7. Store approved images inside assets/projects/<project-id>/screenshots/ and reference relative paths. Never add screenshots copied from private systems unless they are approved for public release.
8. Run python3 scripts/validate.py and review the diff before commit.

## Example catalog entry

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
  "screenshots": []
}
~~~

Replace example values with the real, approved data. The example hostname is illustrative and must not be copied as a project URL.

## Never do these

- Never put a private GitHub repository URL in sourceUrl, description, story, demoNote, image alt text, or a button URL.
- Never assume a private repo means the deployment is private or secure. Deployment permissions are separate.
- Never put tokens, credentials, customer records, production IDs, secret configuration, private endpoints, or useful exploit artifacts in public source files or screenshots.
- Never label an access-controlled app as a public live demo.
- Never link an intentionally vulnerable application until its isolation and deployment access controls have been verified.

Remember: the entire published gallery, JSON, SVG files, screenshots, commit history, and docs are public content.
