# Based on https://pypi.org/project/open-clip-torch/

from dataclasses import dataclass
from dataclasses import field
import datetime
import pathlib
import statistics
import time
from typing import Optional

import cv2
import open_clip
from PIL import Image
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


@dataclass
class ProcessStats:
  config: Config
  file_count: int
  next_time: float = field(default_factory=time.perf_counter)
  start_time: float = field(default_factory=time.perf_counter)
  last_index: int = 0
  last_time: float = field(default_factory=time.perf_counter)

  def output(self, index: int) -> None:
    new_time = time.perf_counter()

    diff_processed = index - self.last_index
    diff_time = new_time - self.last_time
    if diff_processed and diff_time:
      processed_per_minute = diff_processed / (diff_time / 60)
    else:
      processed_per_minute = 0

    wall_time = new_time - self.start_time
    self.config.log(
        f'Done {index} / {self.file_count} files (scored {index} in {wall_time:.01f}s, {processed_per_minute:.01f} per minute)'
    )

    self.last_index = index
    self.last_time = new_time


@dataclass
class CompareFilesResult:
  file_ids_to_add: list[str]
  file_ids_to_update: list[str]
  paths_to_remove: list[pathlib.Path]

  def __str__(self):
    return ', '.join((
        f'Add: {len(self.file_ids_to_add)}',
        f'Update: {len(self.file_ids_to_update)}',
        f'Remove: {len(self.paths_to_remove)}',
    ))


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

    self._model = None
    self._preprocess = None
    self._text_features = None

    self._orb = None

  def process(self) -> None:
    self.process_files()
    self.find_groups()
    self.update_chosen()
    self.result_set.save()

  def process_files(self) -> None:
    self.config.log('Processing files...')
    all_files = list(self.config.input_dir.rglob('*'))
    next_time = 0
    stats = ProcessStats(config=self.config, file_count=len(all_files))

    if self.config.tesser_path:
      tesser_api = tesserocr.PyTessBaseAPI(path=self.config.tesser_path)
    else:
      tesser_api = None

    for index, path in enumerate(all_files):
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
        stats.output(index)
        self.result_set.save()
        self.geocoder.save()
        next_time = time.perf_counter() + 5

      self._update_score(path, tesser_api)

    if tesser_api:
      tesser_api.End()

    stats.output(index)
    self.result_set.save()
    self.geocoder.save()

    self.config.log('Processing done!')

  def _update_score(self, path: pathlib.Path,
                    tesser_api: Optional[tesserocr.PyTessBaseAPI]) -> None:
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
    model, _, preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32', pretrained='laion2b_s34b_b79k')
    model.eval(
    )  # model in train mode by default, impacts some models with BatchNorm or stochastic depth active
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
      text_probs = (100.0 *
                    image_features @ self._text_features.T).softmax(dim=-1)
    return dict(zip(LABELS, text_probs.tolist()[0]))

  def _get_centre(self,
                  image_path: pathlib.Path) -> Optional[tuple[float, float]]:
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
        key=lambda result:
        (INCLUDE_OVERRIDE_ORDER[result.include_override], result.total),
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
    self.config.log(
        f'Chose {chosen_count} (/{self.config.output_count}) images')

  def compare_files(self) -> CompareFilesResult:
    self.config.log('Comparing files...')
    # Find all files in the target folder
    self.config.output_dir.mkdir(parents=True, exist_ok=True)
    existing_path_by_file_id = {
        file.name: file for file in self.config.output_dir.iterdir()
    }
    existing_file_id_set = set(existing_path_by_file_id.keys())

    # Get all chosen files
    chosen_file_id_set = set(
        (file_id for file_id, result in self.result_set.results.items()
         if result.is_chosen))

    needs_update_file_id_set = set(
        (file_id for file_id, result in self.result_set.results.items()
         if result.is_chosen and result.needs_update))

    # Work out what files need to be added/removed
    file_ids_to_add_set = chosen_file_id_set - existing_file_id_set
    file_ids_to_add = list(sorted(file_ids_to_add_set))
    file_ids_to_update = list(
        sorted(needs_update_file_id_set - file_ids_to_add_set))
    file_ids_to_remove = existing_file_id_set - chosen_file_id_set
    paths_to_remove = [
        existing_path_by_file_id[file_id] for file_id in file_ids_to_remove
    ]
    paths_to_remove.sort()

    compare_result = CompareFilesResult(
        file_ids_to_add=file_ids_to_add,
        file_ids_to_update=file_ids_to_update,
        paths_to_remove=paths_to_remove,
    )
    self.config.log(f'Compare result: {compare_result}')
    return compare_result

  def update_files(self) -> None:
    compare_result = self.compare_files()

    self.config.log('Updating files...')

    # Remove old files
    self.config.log(
        f'Removing {len(compare_result.paths_to_remove)} old files...')
    for index, path in enumerate(compare_result.paths_to_remove):
      path.unlink()
      if index % 20 == 0:
        self.config.log(f'  Removed {index}...')

    # Copy new files
    self.config.log(
        f'Copying {len(compare_result.file_ids_to_add)} new files...')
    for index, file_id in enumerate(compare_result.file_ids_to_add):
      result = self.result_set.get_result(file_id)
      output_path = self.config.output_dir / file_id
      cropped = result.get_cropped(self.config)
      cropped.save(output_path, quality=self.config.output_quality)
      if index % 20 == 0:
        self.config.log(f'  Copied {index}...')

    # Update changed files
    self.config.log(
        f'Updating {len(compare_result.file_ids_to_update)} files...')
    for index, file_id in enumerate(compare_result.file_ids_to_update):
      result = self.result_set.get_result(file_id)
      output_path = self.config.output_dir / file_id
      output_path.unlink()
      cropped = result.get_cropped(self.config)
      cropped.save(output_path, quality=self.config.output_quality)
      if index % 20 == 0:
        self.config.log(f'  Updated {index}...')

    self.config.log('Updating done!')
