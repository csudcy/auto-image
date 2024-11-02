# Based on https://github.com/google-research/google-research/tree/master/musiq

import pathlib

MODEL = None


def get_score(image_path: pathlib.Path) -> float:
  global MODEL
  # Only import tf if it's required
  import tensorflow as tf
  import tensorflow_hub as hub

  if MODEL is None:
    MODEL = hub.load('https://www.kaggle.com/models/google/musiq/TensorFlow2/ava/1')

  image_bytes = tf.constant(tf.io.read_file(str(image_path)))
  predict = MODEL.signatures['serving_default']
  prediction = predict(image_bytes)
  return float(prediction['output_0'].numpy())
