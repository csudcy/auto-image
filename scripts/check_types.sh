#!/bin/bash
#
# Check types

# Set some failure conditions
set -o errexit   # Fail on any error
set -o pipefail  # Trace ERR through pipes
set -o errtrace  # Trace ERR through sub-shell commands

uv run pytype --config=./pytype.cfg -o ./.pytype $@
