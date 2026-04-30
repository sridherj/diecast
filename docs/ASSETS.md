# Launch assets — editorial notes

This file is the canonical spec for how Diecast's launch surfaces (`README.md`, `docs/index.html`) and their hero illustrations are wired together. It documents intent so future maintainers (and contributors who want to remix the assets) understand what was deliberate.

## Surfaces

| File | Path | Notes |
|------|------|-------|
| Repo README | `<repo-root>/README.md` | Renders on the GitHub repo page. Install-and-try surface. |
| GitHub Pages landing | `<repo-root>/docs/index.html` | Self-contained — Diecast design tokens inline; loads only Google Fonts from the network. Source: `main` branch, `/docs` folder, configured under repo Settings → Pages. |

## Hero images

| Path | Used by | Notes |
|------|---------|-------|
| `<repo-root>/docs/assets/diecast-wordmark.png` | README hero (path: `docs/assets/diecast-wordmark.png`); Pages hero (path: `assets/diecast-wordmark.png`) | Wordmark mark. |
| `<repo-root>/docs/assets/direction-1-warm-workshop-path-A.final.png` | Pages workshop hero (path: `assets/direction-1-warm-workshop-path-A.final.png`) | Warm-workshop watercolor. Loaded via `<img>` in the landing page. |

Both surfaces resolve to the same physical files — README paths are relative to repo root; the Pages page is served from `docs/`, so its image paths are relative to that directory.

## Editorial notes

- The README leans on the "three failure modes" framing from the project's launch deck for the "Why this exists" section. It deliberately skips the deeper failure-mode tier matrix — README readers want the bottom line, not a taxonomy.
- The README does not pitch the full Diecast vision (Layer-1 + Layer-2 + private agent catalogue). That framing belongs in the launch blog post and the deck. The README is the install-and-try surface.
- Maker-checker is mentioned but not deeply explained. The README points readers to [`docs/maker-checker.md`](maker-checker.md) for the worked example.
- The landing page (`docs/index.html`) carries more of the deck's narrative beats: the warm-workshop hero, the failure list, the "doesn't fix the model, fixes the workflow" pull-quote. Visitors who arrive via Hacker News, the launch blog, or a podcast see this; visitors browsing the repo see the README.
- The landing page is **single-file, self-contained**: no build step, no JavaScript, no external CSS. It loads only Google Fonts. Deployment is "enable Pages on the `main` branch with `/docs` as the source."
- Both surfaces use the locked Diecast design tokens: cream `#F5F4F0` background with a 5px subtle grid, magenta `#D6235C` accent, IBM Plex Mono for headings, DM Sans for body, Caveat for a single display flourish.

## Things deliberately NOT included

- No author / "about the maintainer" block. The project is the artifact; biography lives off-repo.
- No Linear, Jira, Codex, or Copilot mentions in present tense — those are roadmap items (see [`roadmap.md`](roadmap.md)).
- No telemetry mention — telemetry is deferred to v1.1.
- No Discord link — GitHub Discussions is the sole community surface at v1.
- No screenshots of the cast-server UI — to be added once the rebrand lands.
- No GIF demos in this drop — see `docs/assets/gifs/` (added in a follow-up sub-phase).

## Reuse

The wordmark and watercolor are released under the same license as the rest of the repository (Apache-2.0). Attribution: cite "Diecast" and link back to the project. Do not modify the wordmark proportions or recolor the magenta accent — those are part of the brand identity.
