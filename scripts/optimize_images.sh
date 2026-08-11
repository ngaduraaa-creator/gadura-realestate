#!/usr/bin/env bash
# optimize_images.sh — one-off local image optimizer (macOS: sips + cwebp).
# Resizes oversized headshots/photos in /images to a sane max dimension IN PLACE
# (same filename/format → zero HTML-reference risk) and emits a .webp sibling for
# each so Cloudflare Polish / a future <picture> can serve modern formats.
#
# Audit finding (critical CWV): 900KB+ headshots (2500px) rendered at ~80–104px,
# photographic PNGs, zero WebP across 1705 pages — the biggest total-byte win.
#
# Run from repo root:  bash scripts/optimize_images.sh
set -euo pipefail
cd "$(dirname "$0")/.."

MAX=600          # longest-side cap for headshots (2x retina at ~300px display)
THRESH=150000    # only touch files above this many bytes

echo "== optimizing images >$((THRESH/1000))KB to max ${MAX}px longest side =="
total_before=0; total_after=0
for f in images/*.jpg images/*.jpeg images/*.png; do
  [ -f "$f" ] || continue
  before=$(wc -c < "$f")
  [ "$before" -le "$THRESH" ] && continue
  # current longest side — only DOWNSCALE (sips -Z would otherwise upscale small imgs)
  w=$(sips -g pixelWidth "$f" 2>/dev/null | awk '/pixelWidth/{print $2}')
  h=$(sips -g pixelHeight "$f" 2>/dev/null | awk '/pixelHeight/{print $2}')
  longest=$(( w > h ? w : h ))
  if [ "${longest:-0}" -gt "$MAX" ]; then
    sips -Z "$MAX" "$f" >/dev/null 2>&1 || true
  fi
  after=$(wc -c < "$f")
  # webp sibling (quality 82 = visually lossless for headshots)
  webp="${f%.*}.webp"
  cwebp -quiet -q 82 "$f" -o "$webp" >/dev/null 2>&1 || true
  wsz=$( [ -f "$webp" ] && wc -c < "$webp" || echo 0 )
  total_before=$((total_before+before)); total_after=$((total_after+after))
  printf "  %-42s %8d -> %7d bytes  (webp %6d)\n" "$(basename "$f")" "$before" "$after" "$wsz"
done
echo "== source bytes: $total_before -> $total_after (saved $(( (total_before-total_after)/1000 ))KB in-place) =="
