#!/usr/bin/env bash

source .venv/bin/activate

# Run pytest with both terminal and HTML coverage reports
pytest --cov="src/$1" --cov-report=term --cov-report=html .
