#!/bin/bash
#
# Check style

# Set some failure conditions
set -o errexit   # Fail on any error
set -o pipefail  # Trace ERR through pipes
set -o errtrace  # Trace ERR through sub-shell commands

# Check/fix the code styles
uv run yapf --parallel -vv -r ./ $@
