#!/bin/bash
#
# Score dropbox images

./scripts/poetry_run.sh python3 score.py \
  "/Users/csudcy/Library/CloudStorage/Dropbox/Camera Uploads" \
  --output-count=5000 \
  --recent-days=800 \
  --recent-percent=25 \
  "${@}"
