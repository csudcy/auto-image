import json
import os
import tempfile
import time

print('Importing tensorflow & hub...')
import tensorflow as tf
import tensorflow_hub as hub

import score_musiq
import score_vila
import utils

SCORERS = (
    ('musiq', score_musiq.get_score),
    ('vila', score_vila.get_score),
)

IMAGE_LIMIT = None


def _save_scores(scores: dict) -> None:
  with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
      json.dump(scores, temp_file, indent=2)
  os.replace(temp_file.name, utils.SCORE_FILE)


processed = 0
start_time = time.perf_counter()
def _show_stats():
  diff_time = time.perf_counter() - start_time
  if processed:
    processed_per_minute = processed / (diff_time / 60)
  else:
    processed_per_minute = 0
  print(f'Done {index} files (scored {processed} in {diff_time:.02f}s, {processed_per_minute:.02f} per minute)')


print('Predicting...')
SCORES = utils.load_scores()
next_time = start_time
for index, path in enumerate(utils.IMAGE_FOLDER.rglob('*')):
  if IMAGE_LIMIT and index >= IMAGE_LIMIT:
    print('Hit limit; stopping...')
    break

  if time.perf_counter() >= next_time:
    _show_stats()
    next_time = time.perf_counter() + 5
    _save_scores(SCORES)

  # Check if the file has been scored already
  file_id = str(path.relative_to(utils.IMAGE_FOLDER))
  file_scores = SCORES.get(file_id) or {}

  # Process the scores
  for name, score_func in SCORERS:
    # Check if this model has been done already
    if name in file_scores:
      continue
    
    file_scores[name] = score_func(path)
    processed += 1

  # Save results back to scores
  SCORES[file_id] = file_scores

_show_stats()
_save_scores(SCORES)

print('Done!')
