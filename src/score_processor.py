
# Based on https://pypi.org/project/open-clip-torch/

import datetime
import pathlib
import time
from typing import Optional

from PIL import Image
import open_clip
import torch

from src import result_manager

EXTENSIONS = ('jpg', 'png')

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
LABEL_SET = set(LABELS)


class Scorer:

  def __init__(
      self,
      result_set: result_manager.ResultSet,
      image_limit: Optional[int] = None,
  ):
    self.result_set = result_set
    self.image_limit = image_limit

    self._all_files = list(self.result_set.image_folder.rglob('*'))
    self._file_count = len(self._all_files)
    self._overall_processed = 0
    self._overall_time = time.perf_counter()
    self._stats_last_processed = 0
    self._stats_last_time = time.perf_counter()

    self._model = None
    self._preprocess = None
    self._text_features = None

  def process(self) -> None:
    print('Processing files...')
    next_time = self._overall_time
    for index, path in enumerate(self._all_files):
      if self.image_limit and index >= self.image_limit:
        print('Hit limit; stopping...')
        break

      if not path.is_file():
        # Skip directories
        continue

      extension = path.suffix.lower().lstrip('.')
      if extension not in EXTENSIONS:
        print(f'  Skipping non-image: {path.name}')
        continue

      if time.perf_counter() >= next_time:
        self._show_stats(index)
        self.result_set.save()
        next_time = time.perf_counter() + 5
      
      self._update_score(path)

    self._show_stats(index)
    self.result_set.save()

    print('Processing done!')

  def _show_stats(self, index: int) -> None:
    new_time = time.perf_counter()

    diff_processed = self._overall_processed - self._stats_last_processed
    diff_time = new_time - self._stats_last_time
    if diff_processed and diff_time:
      processed_per_minute = diff_processed / (diff_time / 60)
    else:
      processed_per_minute = 0

    wall_time = new_time - self._overall_time
    print(f'Done {index} / {self._file_count} files (scored {self._overall_processed} in {wall_time:.01f}s, {processed_per_minute:.01f} per minute)')

    self._stats_last_processed = self._overall_processed
    self._stats_last_time = new_time

  def _update_score(self, path: pathlib.Path) -> None:
    # Get the result for this path
    result = self.result_set.get_result(path)

    # Process the scores (when necessary)
    if LABEL_SET.difference(result.scores):
      if self._model is None:
        self._init_model()
      self._overall_processed += 1
      try:
        result.scores = self._score(path)
      except Exception as ex:
        print(f'  Error scoring {path.name} - {ex}')
        return

    # Calculate the total
    weighted_score = [
        round(LABEL_WEIGHTS[label] * result.scores[label], 3)
        for label in LABELS
    ]
    result.total = sum(weighted_score)

  def _init_model(self) -> None:
    model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
    model.eval()  # model in train mode by default, impacts some models with BatchNorm or stochastic depth active
    tokenizer = open_clip.get_tokenizer('ViT-B-32')

    text = tokenizer(LABELS)
    text_features = model.encode_text(text)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    self._model = model
    self._preprocess = preprocess
    self._text_features = text_features
  
  def _score(self, image_path: pathlib.Path) -> dict[str, float]:
    # This is supposed to make things faster/more efficient but doesn't seem to do much;
    # however, it does stop memory going crazy & getting the process killed after some time.
    with torch.no_grad(), torch.cuda.amp.autocast():
      image = self._preprocess(Image.open(image_path)).unsqueeze(0)
      image_features = self._model.encode_image(image)
      image_features /= image_features.norm(dim=-1, keepdim=True)
      text_probs = (100.0 * image_features @ self._text_features.T).softmax(dim=-1)
    return dict(zip(LABELS, text_probs.tolist()[0]))

  def update_chosen(
      self,
      recent_delta: datetime.timedelta,
      top_recent_count: int,
      top_old_count: int,
  ) -> None:
    now = datetime.datetime.now()
    recent_minimum = now - recent_delta
    recent_results = []
    old_results = []

    results_list = sorted(
        self.result_set.results.values(),
        key=lambda result: result.total,
        reverse=True,
    )
    for result in results_list:
      result.is_recent = result.taken > recent_minimum
      if result.is_recent:
        recent_results.append(result)
      else:
        old_results.append(result)

    for result in recent_results[:top_recent_count]:
      result.is_chosen = True
    for result in old_results[:top_old_count]:
      result.is_chosen = True
