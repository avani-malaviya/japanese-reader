#!/usr/bin/env sh
# Checks a running copy of the app end to end: health, a reading lookup, and a real OCR run.
#   scripts/smoke.sh http://localhost:8000
set -eu
BASE=${1:-http://localhost:8000}
PAGE="$(dirname "$0")/../backend/tests/fixtures/smoke_page.png"

echo "waiting for $BASE"
for _ in $(seq 1 60); do
  curl -fsS "$BASE/api/health" >/dev/null 2>&1 && break
  sleep 2
done
curl -fsS "$BASE/api/health"; echo

echo "reading lookup"
curl -fsS -H "Content-Type: application/json" -d '{"text": "日本語"}' "$BASE/api/reading" | grep -q "にほんご"

echo "OCR (the first page loads the models, so it can take a while)"
curl -fsS --max-time 600 -F "image=@$PAGE" "$BASE/api/ocr" | grep -q "日本語の本を読みます"

echo "smoke test passed"
