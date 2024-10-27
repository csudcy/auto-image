# Based on https://github.com/google-research/google-research/tree/master/musiq

import tensorflow_hub as hub

MODEL = None


def get_score(image_bytes: bytes) -> float:
  global MODEL
  if MODEL is None:
    MODEL = hub.load('https://www.kaggle.com/models/google/musiq/TensorFlow2/ava/1')

  predict = MODEL.signatures['serving_default']
  prediction = predict(image_bytes)
  return float(prediction['output_0'].numpy())
