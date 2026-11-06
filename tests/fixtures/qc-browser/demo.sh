#!/bin/sh
# The qc browser demo (tests/gate/kit/qc_browser.py): Playwright's headless Chromium shell, found by
# PLAYWRIGHT_BROWSERS_PATH, screenshots the page into $QC_SCREENSHOTS; it fails if the masked cache or a writable
# browser folder shows.
set -e
[ ! -e "$HOME/.cache/ms-playwright/masked-marker" ] || { echo "the masked cache is visible" >&2; exit 9; }
if touch "$PLAYWRIGHT_BROWSERS_PATH/.w" 2>/dev/null; then echo "browser folder writable" >&2; exit 8; fi
# shellcheck disable=SC2012  # one known dir layout, no odd names
shell=$(ls -d "$PLAYWRIGHT_BROWSERS_PATH"/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell | head -1)
"$shell" --no-sandbox --user-data-dir="$TMPDIR/profile" --window-size=640,400 --screenshot="$QC_SCREENSHOTS/page.png" "file://$QC_REPO/page.html"
echo "screenshot taken with $shell"
