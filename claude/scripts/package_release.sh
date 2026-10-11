#!/usr/bin/env bash
# Zabalí repozitář (bez velkých MCMC fitů) do ZIPu a zkopíruje notebook zvlášť.
# Použití: bash scripts/package_release.sh [výstupní_složka]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/dist}"
mkdir -p "$OUT"
NAME="revnice2026_bayes_repo"
rm -f "$OUT/$NAME.zip"
cd "$ROOT/.."
zip -r -q "$OUT/$NAME.zip" "$(basename "$ROOT")" \
  -x "*/fits/*.nc" "*/fits/*.npz" "*/__pycache__/*" "*.pyc" "*/.ipynb_checkpoints/*" "*/dist/*" "*/.pytest_cache/*"
cp "$ROOT/revnice_2026_bayesian_analysis.ipynb" "$OUT/"
ls -la "$OUT"
