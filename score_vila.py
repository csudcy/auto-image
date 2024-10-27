# Based on https://www.kaggle.com/models/google/vila

import pathlib

import tensorflow as tf
import tensorflow_hub as hub

MODEL = None


def get_score(image_path: pathlib.Path) -> float:
  global MODEL
  if MODEL is None:
    MODEL = hub.load('https://tfhub.dev/google/vila/image/1')

  image_bytes = tf.constant(tf.io.read_file(str(image_path)))
  predict = MODEL.signatures['serving_default']
  prediction = predict(image_bytes)
  return float(prediction['predictions'].numpy()[0][0]) * 10
