
# Based on https://pypi.org/project/open-clip-torch/

import datetime
import pathlib
import statistics
import time
from typing import Optional

import cv2
from PIL import Image
import open_clip
import tesserocr
import torch

from src import geocode_manager
from src import result_manager
from src.config import Config

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

INCLUDE_OVERRIDE_ORDER = {
    # Included images should be first (so they should be included before hitting the limit)
    True: 0,
    # Non-overridden images next
    None: 1,
    # Then excluded images (which don't really need to be here, but meh)
    False: 2,
}


class Scorer:

  def __init__(
      self,
      config: Config,
      result_set: result_manager.ResultSet,
      geocoder: geocode_manager.GeoCoder,
  ):
    self.config = config
    self.result_set = result_set
    self.geocoder = geocoder

    self._all_files = list(self.config.input_dir.rglob('*'))
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
    self.config.log('Processing files...')
    next_time = self._overall_time

    if self.config.tesser_path:
      tesser_api = tesserocr.PyTessBaseAPI(path=self.config.tesser_path)
    else:
      tesser_api = None

    for index, path in enumerate(self._all_files):
      if self.config.max_images and index >= self.config.max_images:
        self.config.log('Hit limit; stopping...')
        break

      if not path.is_file():
        # Skip directories
        continue

      if path.name == '.DS_Store':
        continue
      extension = path.suffix.lower().lstrip('.')
      if extension not in EXTENSIONS:
        if extension not in HIDE_SKIP_EXTENSIONS:
          self.config.log(f'  Skipping non-image: {path.name}')
        continue

      if time.perf_counter() >= next_time:
        self._show_stats(index)
        self.result_set.save()
        self.geocoder.save()
        next_time = time.perf_counter() + 5

      self._update_score(path, tesser_api)

    if tesser_api:
      tesser_api.End()

    self._show_stats(index)
    self.result_set.save()
    self.geocoder.save()

    self.config.log('Processing done!')

  def _show_stats(self, index: int) -> None:
    new_time = time.perf_counter()

    diff_processed = self._overall_processed - self._stats_last_processed
    diff_time = new_time - self._stats_last_time
    if diff_processed and diff_time:
      processed_per_minute = diff_processed / (diff_time / 60)
    else:
      processed_per_minute = 0

    wall_time = new_time - self._overall_time
    self.config.log(f'Done {index} / {self._file_count} files (scored {self._overall_processed} in {wall_time:.01f}s, {processed_per_minute:.01f} per minute)')

    self._stats_last_processed = self._overall_processed
    self._stats_last_time = new_time

  def _update_score(self, path: pathlib.Path, tesser_api: Optional[tesserocr.PyTessBaseAPI]) -> None:
    # Get the result for this path
    result = self.result_set.get_result(path.name)
    path = path.absolute()

    if result.path and result.path != path:
      self.config.log('\n'.join((
          f'  Duplicate file: {path.name}',
          f'    -> {result.path}',
          f'    -> {path}',
      )))
      return

    self._overall_processed += 1
    result.path = path

    # Find the centre (when necessary)
    if not result.centre:
      result.centre = self._get_centre(result.path)

    # Find the location (when necessary)
    if not result.lat_lon_extracted:
      result.lat_lon = self.geocoder.extract_lat_lon(result.image)
      result.lat_lon_extracted = True
    if result.lat_lon:
      result.location = self.geocoder.get_name(result.lat_lon)

    if tesser_api and result.ocr_text is None:
      tesser_api.SetImage(result.image)
      result.ocr_text = tesser_api.GetUTF8Text()
      if result.ocr_text:
        # boxes = tesser_api.GetComponentImages(tesserocr.RIL.TEXTLINE, True)
        boxes = tesser_api.GetComponentImages(tesserocr.RIL.BLOCK, True)
        text_pixels = 0
        for _, box, _, _ in boxes:
          text_pixels += box['w'] * box['h']
        image_pixels = result.image.size[0] * result.image.size[1]
        result.ocr_coverage = text_pixels / image_pixels

    # Process the scores (when necessary)
    if LABEL_SET.difference(result.scores):
      if self._model is None:
        self._init_model()
      try:
        result.scores = self._score(result.image)
      except Exception as ex:
        self.config.log(f'  Error scoring {result.path.name} - {ex}')
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
  
  def _score(self, image: Image.Image) -> dict[str, float]:
    # This is supposed to make things faster/more efficient but doesn't seem to do much;
    # however, it does stop memory going crazy & getting the process killed after some time.
    with torch.no_grad(), torch.cuda.amp.autocast():
      processed_image = self._preprocess(image).unsqueeze(0)
      image_features = self._model.encode_image(processed_image)
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
    self.config.log('Grouping images...')
    results_list = sorted(
        self.result_set.results.values(),
        key=lambda result: result.taken or datetime.datetime.min,
    )
    # Reset all groups
    for result in results_list:
      result.group_index = None
    groups = []
    previous_result: result_manager.Result = results_list[0]
    result: result_manager.Result
    for result in results_list[1:]:
      if result.taken and previous_result.taken:
        delta = result.taken - previous_result.taken
        if delta <= maximum_delta:
          if previous_result.group_index is None:
            groups.append([previous_result])
            previous_result.group_index = len(groups)
          groups[-1].append(result)
          result.group_index = previous_result.group_index
      previous_result = result
    self.config.log(f'Found {len(groups)} group(s)!')
    return groups

  def update_chosen(self) -> None:
    results_list: list[result_manager.Result] = sorted(
        self.result_set.results.values(),
        key=lambda result: (INCLUDE_OVERRIDE_ORDER[result.include_override], result.total),
        reverse=True,
    )
    used_groups = []
    chosen_count = 0
    for result in results_list:
      if result.include_override != True and any((
          # This image doesn't exist
          result.path is None,
          # This image doesn't score enough
          result.total < self.config.minimum_score,
          # This group has already been chosen already
          result.group_index in used_groups,
          # Too much text
          all((
              (result.ocr_coverage or 0) >= self.config.ocr_coverage_threshold,
              len(result.ocr_text or '') >= self.config.ocr_text_threshold,
          )),
          # This result has been specifically excluded
          result.include_override == False,
      )):
        continue
 
      if chosen_count < self.config.output_count:
        result.is_chosen = True
        chosen_count += 1
      if result.is_chosen and result.group_index is not None:
        used_groups.append(result.group_index)
    self.config.log(f'Chose {chosen_count} (/{self.config.output_count}) images')
