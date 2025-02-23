#!/bin/bash
#
# Update backend dependencies

# Set some failure conditions
set -o errexit   # Fail on any error
set -o pipefail  # Trace ERR through pipes
set -o errtrace  # Trace ERR through sub-shell commands

echo "Updating dependencies..."
uv python install
uv lock --upgrade
uv sync --frozen

echo "Generating requirements.txt files..."
uv export > requirements.txt
