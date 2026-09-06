#!/usr/bin/env bash
# Downloads your 8 ELUSOC badge images into the repo so they keep working
# even if edulinkup.dev blocks hotlinking or goes offline.
# Run once from the repo root:  bash tools/vendor-elusoc-badges.sh
set -euo pipefail

BASE="https://www.edulinkup.dev/elusoc/images/ticket"
OUT="assets/elusoc"
mkdir -p "$OUT"

for b in spawnling stone_coder iron_developer gold_engineer \
         diamond_architect end_conqueror netherite_champion repo_legend; do
  if curl -sfL --max-time 30 "$BASE/$b.png" -o "$OUT/$b.png"; then
    echo "ok    $b.png"
  else
    echo "FAIL  $b.png  (badge may have moved — grab it from your ELUSOC profile)"
  fi
done

echo
echo "Now swap the URLs in README.md:"
echo "  Find:    https://www.edulinkup.dev/elusoc/images/ticket/"
echo "  Replace: ./assets/elusoc/"
