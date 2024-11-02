# Based on https://pypi.org/project/open-clip-torch/

import pathlib

from PIL import Image
import open_clip

LABEL_WEIGHTS = {
    'an interesting photo': 5,

    'a photo of animals': 3,

    'a photo of a dog': 2,
    'a photo of a cat': 2,
    'a fun photo': 2,
    'a photo of people': 2,

    'a photo of a concert': 1,
    'a photo of a festival': 1,
    'a photo of the theatre': 1,

    'lots of text': -2,

    'a persons bare skin': -4,
    'a screenshot': -4,
    'a photo of a document': -4,

    'a boring photo': -5,
}
LABELS = list(LABEL_WEIGHTS.keys())

MODEL = None


class Model:

  def __init__(self):
    model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
    model.eval()  # model in train mode by default, impacts some models with BatchNorm or stochastic depth active
    tokenizer = open_clip.get_tokenizer('ViT-B-32')

    text = tokenizer(LABELS)
    text_features = model.encode_text(text)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    self.model = model
    self.preprocess = preprocess
    self.text_features = text_features
  
  def score(self, image_path: pathlib.Path) -> dict[str, float]:
    image = self.preprocess(Image.open(image_path)).unsqueeze(0)
    image_features = self.model.encode_image(image)
    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_probs = (100.0 * image_features @ self.text_features.T).softmax(dim=-1)
    return dict(zip(LABELS, text_probs.tolist()[0]))


def get_score(image_path: pathlib.Path) -> float:
  global MODEL
  if MODEL is None:
    MODEL = Model()
  return MODEL.score(image_path)


def classify(score: dict[str, float]) -> int:
  return [
      round(LABEL_WEIGHTS[label] * score[label], 3)
      for label in LABELS
  ]
