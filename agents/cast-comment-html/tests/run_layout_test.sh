#!/usr/bin/env bash
# Run the DOM wrap-layout regression test (tests/test_wrap_layout.html) in headless Chrome.
#
# This guards a layout bug that pure-node tests structurally cannot reach: wrapRange() must not
# inject a stray <mark> as a grid/flex/table child (see the file's header comment). It needs a real
# layout engine, so it runs in Chrome and asserts the page reports "PASS".
#
# Skips cleanly (exit 0) when no Chrome/Chromium is installed, so it never breaks a headless CI box
# that has no browser. Run it locally before touching the highlight code.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAGE="file://${HERE}/test_wrap_layout.html"

CHROME=""
for c in google-chrome google-chrome-stable chromium chromium-browser chrome; do
  if command -v "$c" >/dev/null 2>&1; then CHROME="$c"; break; fi
done
if [ -z "$CHROME" ]; then
  echo "SKIP  test_wrap_layout: no Chrome/Chromium found on PATH" >&2
  exit 0
fi

OUT="$("$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --virtual-time-budget=5000 --dump-dom "$PAGE" 2>/dev/null || true)"

RESULT="$(printf '%s' "$OUT" | grep -oE 'id="__result__">[^<]*' | head -1 | sed 's/^id="__result__">//')"

if [ "$RESULT" = "PASS" ]; then
  echo "  ok  test_wrap_layout: grid / flex / table / block flow preserved on comment"
  exit 0
fi
echo "FAIL  test_wrap_layout: ${RESULT:-no result (page did not run)}" >&2
exit 1
