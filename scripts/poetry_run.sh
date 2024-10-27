#!/bin/bash
#
# Execute a command using poetry (after checking that the env has been setup)

# Change to the parent directory
cd "${BASH_SOURCE%/*}"
cd ..

if [ -z "$(poetry env list)" ]; then
  ./scripts/poetry_install.sh
fi

poetry run $@
