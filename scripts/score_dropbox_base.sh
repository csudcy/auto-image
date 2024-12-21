#!/bin/bash
#
# Score dropbox images

./scripts/poetry_run.sh python3 score.py \
  "/Users/csudcy/Library/CloudStorage/Dropbox/Camera Uploads" \
  --output-count=5000 \
  --recent-days=800 \
  --exclude-date=20160502 \
  --exclude-date=20170204 \
  --exclude-date=20170205 \
  --exclude-date=20170206 \
  --exclude-date=20170224 \
  --exclude-date=20170426 \
  --recent-percent=25 \
  "${@}"
