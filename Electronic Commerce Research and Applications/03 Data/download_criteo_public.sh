#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-data/raw/criteo}"
mkdir -p "$OUT_DIR"

ATTRIBUTION_URL="https://criteostorage.blob.core.windows.net/criteo-research-datasets/criteo_attribution_dataset.zip"
UPLIFT_URL="https://criteostorage.blob.core.windows.net/criteo-research-datasets/criteo-uplift-v2.1.csv.gz"

echo "Downloading Criteo Attribution Modeling for Bidding dataset..."
curl -fL "$ATTRIBUTION_URL" -o "$OUT_DIR/criteo_attribution_dataset.zip"

echo "Downloading Criteo Uplift unbiased v2.1 dataset..."
curl -fL "$UPLIFT_URL" -o "$OUT_DIR/criteo-uplift-v2.1.csv.gz"

if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "$OUT_DIR/criteo_attribution_dataset.zip" "$OUT_DIR/criteo-uplift-v2.1.csv.gz" \
    > "$OUT_DIR/SHA256SUMS.txt"
elif command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "$OUT_DIR/criteo_attribution_dataset.zip" "$OUT_DIR/criteo-uplift-v2.1.csv.gz" \
    > "$OUT_DIR/SHA256SUMS.txt"
fi

echo "Download complete. Raw files are intentionally not committed to GitHub."
