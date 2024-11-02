# Based on https://www.kaggle.com/models/google/vila

import pathlib

MODEL = None


def get_score(image_path: pathlib.Path) -> float:
  global MODEL
  # Only import tf if it's required
  import tensorflow as tf
  import tensorflow_hub as hub

  if MODEL is None:
    MODEL = hub.load('https://tfhub.dev/google/vila/image/1')

  image_bytes = tf.constant(tf.io.read_file(str(image_path)))
  predict = MODEL.signatures['serving_default']
  prediction = predict(image_bytes)
  return float(prediction['predictions'].numpy()[0][0]) * 10


def classify(score: float) -> int:
  if score <= 3:
    return -1
  else:
    return 0
