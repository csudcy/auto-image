#!/bin/bash
#
# Update poetry dependencies

# Set some failure conditions
set -o errexit   # Fail on any error
set -o pipefail  # Trace ERR through pipes
set -o errtrace  # Trace ERR through sub-shell commands

# Change to the parent directory
cd "${BASH_SOURCE%/*}"
cd ..

echo "Updating dependencies..."
poetry update

echo "Generating requirements.txt file..."
poetry export --format=requirements.txt --without-hashes > requirements.txt
