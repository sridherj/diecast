# Spike 1b Result — Dual viewer + in-frame commenting

**Verdict: VIABLE → in-viewer commenting via `<iframe srcdoc>` + postMessage bridge.**
(NOT the full-page fallback.) Validated 2026-06-20 in Chrome against a real
`refined_requirements.html` embedded in the exact 2b sandbox config.

## Evidence
- **SC-A (srcdoc render + isolation): PASS.** The full standalone requirements render embeds
  cleanly inside `<iframe srcdoc sandbox="allow-scripts allow-popups">`. No `<head>/<style>`
  collision: the host page's aggressive `h1{color:red!important}` did NOT bleed into the iframe
  (render heading stayed its own dark style); the render's own typography/layout intact.
- **In-iframe selection + comment authoring: PASS.** Inside the null-origin srcdoc frame, text
  selection works, the cast-comment-html "+ Comment" affordance appears, the composer opens, and a
  comment is authored + anchored (quote highlighted in-doc, tray shows "Feedback · 1").
- **postMessage bridge (iframe→host): PASS (probe-confirmed).** A null-origin sandboxed srcdoc
  iframe (`allow-scripts`, NO `allow-same-origin`) postMessages to the host:
  `e.source === iframe.contentWindow` is **true**, `e.origin === "null"`.

## Confirms plan-review Issue #3 (binding for 3b)
- Inbound guard MUST match on **source identity** (`event.source === contentWindow`), NOT origin
  (origin is `"null"` for srcdoc).
- Reply into the frame MUST use `targetOrigin="*"` (cannot target `"null"`).
- Multi-iframe → maintain an `artifact_ref → contentWindow` registry; route replies to the origin frame.

## Note for 3b implementation
Replace cast-comment-html `comment-layer.js`'s `submit()` transport (`fetch(CFG.submit)`) DIRECTLY
with `window.parent.postMessage({comments[], goal_slug, artifact_ref}, '*')` — do NOT rely on a
global `fetch` override (the spike harness used a fetch-shim that didn't intercept the layer's call;
direct transport replacement is the clean path).
