
# Based on https://pypi.org/project/open-clip-torch/

import datetime
import pathlib
import statistics
import time
from typing import Optional

import cv2
from PIL import Image
import open_clip
import torch

from src import result_manager

EXTENSIONS = ('jpg', 'png')
HIDE_SKIP_EXTENSIONS = ('mp4', 'html', 'gif', 'json')

PHRASE_GOOD = ' '.join((
    'A photo thats interesting or fun, with a good subject.',
    'A photo thats safe for work photo - people, animals, nature, etc.',
    'A photo thats nice and clear & not blurry.',
))
PHRASE_BAD = ' '.join((
    'A photo thats featureless or boring with no subject.',
    'A photo thats not safe for work - bare skin, injuries, etc.',
    'A photo of a document, screenshot, or lots of text.',
    'A photo thats blurry and unclear.',
))
LABEL_WEIGHTS = {
  PHRASE_GOOD: 5,
  PHRASE_BAD: -5,
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

    self._orb = None

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
        if extension not in HIDE_SKIP_EXTENSIONS:
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
    result = self.result_set.get_result(path.name)

    if result.path:
      print('\n'.join((
          f'  Duplicate file: {path.name}',
          f'    -> {result.path}',
          f'    -> {path}',
      )))
      return
    else:
      result.path = path

    # Find the centre (when necessary)
    if not result.centre:
      self._overall_processed += 1
      result.centre = self._get_centre(path)

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

  def _get_centre(self, image_path: pathlib.Path) -> Optional[tuple[float, float]]:
    # Load the image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Create an ORB object
    if self._orb is None:
      self._orb = cv2.ORB_create()

    # Detect key points and compute descriptors
    key_points = self._orb.detect(image)

    if key_points:
      c_x = int(statistics.mean(kp.pt[0] for kp in key_points))
      c_y = int(statistics.mean(kp.pt[1] for kp in key_points))
      return (c_x, c_y)
    else:
      return None

  def find_groups(
      self,
      maximum_delta: datetime.timedelta = datetime.timedelta(seconds=8),
  ) -> list[list[result_manager.Result]]:
    print('Grouping images...')
    results_list = sorted(
        self.result_set.results.values(),
        key=lambda result: result.taken,
    )
    groups = []
    previous_result: result_manager.Result = results_list[0]
    result: result_manager.Result
    for result in results_list[1:]:
      delta = result.taken - previous_result.taken
      if delta <= maximum_delta:
        if previous_result.group_index is None:
          groups.append([previous_result])
          previous_result.group_index = len(groups)
        groups[-1].append(result)
        result.group_index = previous_result.group_index
      previous_result = result
    print(f'Found {len(groups)} group(s)!')
    return groups

  def update_chosen(
      self,
      recent_delta: datetime.timedelta,
      minimum_score: float,
      top_recent_count: int,
      top_old_count: int,
      exclude_dates: list[datetime.date],
  ) -> None:
    now = datetime.datetime.now()
    recent_minimum = now - recent_delta

    results_list: list[result_manager.Result] = sorted(
        self.result_set.results.values(),
        key=lambda result: result.total,
        reverse=True,
    )
    used_groups = []
    recent_chosen_count = 0
    old_chosen_count = 0
    for result in results_list:
      result.is_recent = result.taken > recent_minimum

      if any((
          # This image doesn't exist
          result.path is None,
          # This image doesn't score enough
          result.total < minimum_score,
          # This date is excluded
          result.taken.date() in exclude_dates,
          # This group has already been chosen already
          result.group_index in used_groups,
      )):
        continue
 
      if result.is_recent:
        if recent_chosen_count < top_recent_count:
          result.is_chosen = True
          recent_chosen_count += 1
      else:
        if old_chosen_count < top_old_count:
          result.is_chosen = True
          old_chosen_count += 1
      if result.is_chosen and result.group_index is not None:
        used_groups.append(result.group_index)
    print(f'Chose {recent_chosen_count} (/{top_recent_count}) recent & {old_chosen_count} (/{top_old_count}) old')
