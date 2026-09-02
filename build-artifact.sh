#!/usr/bin/env bash
# Reassemble report.body.html from the two Jekyll includes.
#
# The report has a single source, split for Jekyll:
#   _includes/report-head.html  -> <title>, font links, <style>
#   _includes/report-body.html  -> page markup + <script>
#
# Jekyll assembles them through _layouts/report.html. This script produces the
# other target: the flat fragment published as a Claude Artifact, which supplies
# its own <!doctype>/<head>/<body> wrapper at publish time.
#
# Edit the includes, never report.body.html — it is generated.
set -euo pipefail
cd "$(dirname "$0")"

OUT="report.body.html"

for f in _includes/report-head.html _includes/report-body.html; do
  [[ -f "$f" ]] || { echo "build-artifact: $f not found" >&2; exit 1; }
done

{
  cat _includes/report-head.html
  echo
  cat _includes/report-body.html
} > "$OUT"

echo "build-artifact: wrote $OUT ($(wc -c < "$OUT") bytes)"
