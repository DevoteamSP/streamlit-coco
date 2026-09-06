#!/usr/bin/env bash
# Fetch the optional 17 MB Microsoft samples (not committed).
set -euo pipefail
cd "$(dirname "$0")"
MS=https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main
curl -fsSL -o "Human Resources Sample PBIX.pbix" \
  "$MS/Sample%20Reports/Human%20Resources%20Sample%20PBIX.pbix"
curl -fsSL -o "Employee Hiring and History.pbix" \
  "$MS/new-power-bi-service-samples/Employee%20Hiring%20and%20History.pbix"
ls -la "Human Resources Sample PBIX.pbix" "Employee Hiring and History.pbix"
