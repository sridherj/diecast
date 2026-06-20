# sp2b Dual Viewer — Post-Execution Review Follow-ups

Source: cast-subphase-runner B4 inline review (cast-review-code runs in a new
terminal tab the autonomous runner cannot drive; review performed inline per the
runner's non-delegated-inline rule, server was up but the terminal-tab gate is
not autonomously observable — noted honestly).

## Non-blocking notes (no auto-fix applied — confidence: low/medium, deferred)

1. **iframe `onload` height-fit is a no-op under null-origin (low).** The macro's
   `onload="...this.contentDocument.documentElement.scrollHeight..."` reads
   `contentDocument`, which is `null` for a sandbox WITHOUT `allow-same-origin`
   (this IS the null origin we want). The try/catch swallows it; the iframe falls
   back to the CSS `.artifact-html-frame { min-height: 480px }` floor — correct and
   safe, matches the plan's "generous min-height + scroll OR a one-line onload
   height-fit" guidance. The REAL auto-resize is a postMessage height handshake the
   plan explicitly **defers to Phase 3b** (which owns the bridge). Action for 3b:
   replace the no-op onload with the postMessage height handshake when the bridge
   lands; optionally drop the dead onload then. Not fixed here (multi-consideration
   judgment, not a safe single-Edit; Phase 3b owns this seam).

## Verified clean (no follow-up)
- srcdoc byte-exact round-trip + single parsed `<script>` (adversarial test green).
- sandbox omits `allow-same-origin`; includes `allow-scripts` for the 3b bridge.
- md path byte-identical (kind="markdown" default param).
- read gate admits `.html`; edit gate still rejects it; path-traversal guard reused.
