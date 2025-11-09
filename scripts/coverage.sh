#!/usr/bin/env bash

source .venv/bin/activate

package_name=$(echo "$1" | tr '-' '_')

# Run pytest with coverage reports and tee output
mkdir -p htmlcov
pytest --cov="src/$package_name" --cov-report=html --cov-report=term-missing . 2>&1 | tee htmlcov/coverage_report.txt

# Extract just the missing coverage summary
grep -A 20 "Missing" htmlcov/coverage_report.txt > htmlcov/missing_coverage.txt || true
