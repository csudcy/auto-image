#!/bin/bash
#
# Install poetry dependencies

# Set some failure conditions
set -o errexit   # Fail on any error
set -o pipefail  # Trace ERR through pipes
set -o errtrace  # Trace ERR through sub-shell commands

# Change to the parent directory
cd "${BASH_SOURCE%/*}"
cd ..

poetry env list | while read LINE ; do
  VERSION="${LINE%" (Activated)"}"
  echo "Removing old env... ${VERSION}"
  poetry env remove "${VERSION}"
done

echo "Upgrading pip..."
poetry run pip install --upgrade pip

echo "Installing dependencies..."
poetry install $@
