#!/usr/bin/env bash
set -euo pipefail

# Prerequisites:
# 1. Install Kaggle CLI: pip install kaggle
# 2. Configure Kaggle credentials
# 3. Accept the IEEE-CIS Fraud Detection competition rules in the browser

OUT_DIR="${1:-data/raw/ieee-cis}"
mkdir -p "$OUT_DIR"
kaggle competitions download -c ieee-fraud-detection -p "$OUT_DIR"
echo "Downloaded competition archive to $OUT_DIR. Do not commit raw competition files to GitHub."
