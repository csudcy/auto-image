import json
import os
import tempfile
import time

import utils

print('Importing tensorflow...')
import tensorflow as tf

print('Importing tensorflow-hub...')
import tensorflow_hub as hub

IMAGE_LIMIT = None


print('Loading model...')
# https://github.com/google-research/google-research/tree/master/musiq
model = hub.load('https://www.kaggle.com/models/google/musiq/TensorFlow2/ava/1')
predict = model.signatures['serving_default']


def _save_scores(scores: dict) -> None:
  with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
      json.dump(scores, temp_file, indent=2)
  os.replace(temp_file.name, utils.SCORE_FILE)


print('Predicting...')
SCORES = utils.load_scores()
processed = 0
start_time = time.perf_counter()
next_time = start_time
for index, path in enumerate(utils.IMAGE_FOLDER.rglob('*')):
  if IMAGE_LIMIT and index >= IMAGE_LIMIT:
    print('Hit limit; stopping...')
    break

  if time.perf_counter() >= next_time:
    current_time = time.perf_counter()
    diff_time = current_time - start_time
    if processed:
      processed_per_minute = processed / (diff_time / 60)
    else:
      processed_per_minute = 0
    print(f'Done {index} files (scored {processed} in {diff_time:.02f}s, {processed_per_minute:.02f} per minute)')
    next_time = current_time + 5
    _save_scores(SCORES)

  # Check if the file has been scored already
  file_id = str(path.relative_to(utils.IMAGE_FOLDER))
  if file_id in SCORES:
    continue

  # Process the image
  image_bytes = tf.constant(tf.io.read_file(str(path)))
  prediction = predict(image_bytes)
  SCORES[file_id] = float(prediction['output_0'].numpy())
  processed += 1

_save_scores(SCORES)

print('Done!')
