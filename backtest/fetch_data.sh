#!/usr/bin/env bash
# Download the 1-minute US index ETF dataset used by the backtest.
#
# Source: github.com/kfhoo88/ibkr-scalper  (data/historical/*_IBKR_1min_1year_*.csv)
#   - QQQ / SPY 1-minute RTH bars, 2024-10-31 -> 2025-11-07 (256 sessions, 390 bars/day)
#   - 99,300 rows per symbol, no gaps inside a session, no nulls
#
# The files are fetched through the GitHub API (raw media) so the script also
# works in sandboxes where raw.githubusercontent.com is blocked.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$ROOT/data"
mkdir -p "$DATA_DIR"

REPO="kfhoo88/ibkr-scalper"
BRANCH="main"

fetch() {
  local sym="$1"
  local path="data/historical/${sym}_IBKR_1min_1year_20251110.csv"
  local out="$DATA_DIR/${sym}_1min.csv"
  echo "-> $sym"

  # 1) GitHub API raw media (works without auth, 60 req/h)
  if curl -fsSL -H "Accept: application/vnd.github.raw" \
      "https://api.github.com/repos/${REPO}/contents/${path}?ref=${BRANCH}" \
      -o "$out" 2>/dev/null && [ "$(wc -c <"$out")" -gt 1000000 ]; then
    echo "   ok (github api): $(wc -l <"$out") lines"
    return 0
  fi

  # 2) fall back to the whole-repo tarball via codeload
  echo "   api failed, falling back to codeload tarball..."
  local tmp
  tmp="$(mktemp -d)"
  curl -fsSL "https://codeload.github.com/${REPO}/tar.gz/refs/heads/${BRANCH}" \
       -o "$tmp/repo.tgz"
  tar xzf "$tmp/repo.tgz" -C "$tmp"
  cp "$tmp"/*/"$path" "$out"
  rm -rf "$tmp"
  echo "   ok (codeload): $(wc -l <"$out") lines"
}

for s in QQQ SPY; do fetch "$s"; done

echo
echo "Data ready in $DATA_DIR"
ls -la "$DATA_DIR"
