import dataclasses
import datetime
from io import BytesIO
import json
import os
import pathlib
import re
import tempfile
from typing import Optional

import cachetools
from PIL import Image
from PIL import ImageDraw
from PIL import ImageOps

from src.config import Config

# 2024-10-21 10.52.09-1.jpg
# skin-2018-07-18 12.59.08-2.jpg
# IMG_20240608_141605_1.jpg
DATETIME_RE = r'.*(\d{4}-?\d{2}-?\d{2}[ _]\d{2}.?\d{2}.?\d{2})'
# IMG-20161101-WA0000.jpg
DATE_RE = r'.*(\d{4}-?\d{2}-?\d{2})'
DATETIME_FORMAT = '%Y%m%d %H%M%S'

IMAGE_CACHE = cachetools.LRUCache(maxsize=128)
CROP_CACHE = cachetools.LRUCache(maxsize=128)


@dataclasses.dataclass
class LatLon:
  lat: float
  lon: float


@dataclasses.dataclass
class Result:
  file_id: str
  scores: dict[str, dict[str, float]]

  # Loaded from dict
  centre: Optional[tuple[float, float]] = None
  group_index: Optional[int] = None
  include_override: Optional[bool] = None
  is_chosen: bool = False
  lat_lon: Optional[LatLon] = None
  lat_lon_extracted: bool = False
  location: Optional[str] = None
  needs_update: bool = False
  ocr_coverage: Optional[float] = None
  ocr_text: Optional[str] = None
  path: Optional[pathlib.Path] = None
  total: float = 0

  # Recalculated each time
  taken: Optional[datetime.datetime] = None

  def get_time_taken_text(self, config: Config) -> Optional[str]:
    if self.taken:
      return self.taken.strftime(config.taken_format)
    else:
      return None

  @property
  def image(self) -> Image.Image:
    if self.path:
      return load_image(self.path)
    else:
      raise Exception(f'Can\'t get image when path is not set! {self.file_id}')

  @classmethod
  def parse_filename(cls, file_id: str,
                     config: Config) -> Optional[datetime.datetime]:
    # Parse the datetime from the filename
    if match := re.match(DATETIME_RE, file_id):
      dt = match.group(1)
    elif match := re.match(DATE_RE, file_id):
      dt = f'{match.group(1)} 000000'
    else:
      config.log(f'  Unable to parse date: {file_id}')
      return None

    dt = dt.replace('-', '')
    dt = dt.replace('.', '')
    dt = dt.replace('_', ' ')
    return datetime.datetime.strptime(dt, DATETIME_FORMAT)

  @classmethod
  def from_dict(cls, data: dict, config: Config) -> 'Result':
    if lat_lon_data := data.pop('lat_lon'):
      lat_lon = LatLon(**lat_lon_data)
    else:
      lat_lon = None

    if path_data := data.pop('path'):
      path_potential = pathlib.Path(path_data)
      if path_potential.exists():
        path = path_potential
    else:
      path = None

    return Result(
        centre=data['centre'],
        file_id=data['file_id'],
        group_index=data['group_index'],
        include_override=data['include_override'],
        is_chosen=data['is_chosen'],
        lat_lon=lat_lon,
        lat_lon_extracted=data['lat_lon_extracted'],
        location=data['location'],
        needs_update=data.get('needs_update', False),
        ocr_coverage=data['ocr_coverage'],
        ocr_text=data['ocr_text'],
        path=path,
        scores=data['scores'],
        taken=Result.parse_filename(data['file_id'], config),
        total=data['total'],
    )

  def to_dict(self) -> dict:
    return {
        'centre': self.centre,
        'file_id': self.file_id,
        'group_index': self.group_index,
        'include_override': self.include_override,
        'is_chosen': self.is_chosen,
        'lat_lon': dataclasses.asdict(self.lat_lon) if self.lat_lon else None,
        'lat_lon_extracted': self.lat_lon_extracted,
        'location': self.location,
        'needs_update': self.needs_update,
        'ocr_coverage': self.ocr_coverage,
        'ocr_text': self.ocr_text,
        'path': str(self.path) if self.path else None,
        'scores': self.scores,
        'total': self.total,
    }

  def update_include_override(self, include_override: Optional[bool]) -> None:
    self.include_override = include_override
    if self.include_override == True:
      self.is_chosen = True
    elif self.include_override == False:
      self.is_chosen = False
    # Otherwise, this will need to be updated next time processing is done

  def get_cropped(self, config: Config) -> Image.Image:
    # return _get_cropped(config, self)
    image_width, image_height = self.image.size
    if self.centre:
      centre = (self.centre[0] / image_width, self.centre[1] / image_height)
    else:
      centre = (0.5, 0.5)
    cropped = ImageOps.fit(self.image, (config.crop_width, config.crop_height),
                           centering=centre)

    draw = ImageDraw.Draw(cropped)

    def _draw_text(x: int, y: int, text: str) -> None:
      # Text & outline
      draw.text(
          (x, y),
          text,
          config.font_colour,
          font=config.font,
          stroke_width=config.font_outline_width,
          stroke_fill=config.font_outline_colour,
      )

    # Add location
    text_top = config.crop_height + config.text_offset_y
    if self.location:
      _draw_text(config.text_offset_x, text_top, self.location)
    if self.taken:
      taken_text = self.get_time_taken_text(config)
      if taken_text:
        taken_size = int(draw.textlength(taken_text, font=config.font))
        taken_x = config.crop_width - taken_size - 2 * config.text_offset_x
        _draw_text(taken_x, text_top, taken_text)

    return cropped

  @cachetools.cached(CROP_CACHE, key=lambda self, _: f'{self.file_id}')
  def get_cropped_bytes(self, config: Config) -> bytes:
    cropped = self.get_cropped(config)
    img_io = BytesIO()
    cropped.save(img_io, 'JPEG', quality=config.output_quality)
    img_io.seek(0)
    return img_io.getvalue()


@cachetools.cached(IMAGE_CACHE)
def load_image(path: pathlib.Path) -> Image.Image:
  return Image.open(path)


class ResultSet:

  def __init__(self, config: Config):
    self.config = config
    self.path = self.config.input_dir / '_auto_image.json'
    self.results: dict[str, Result] = {}
    if self.path.exists():
      with self.path.open('r') as f:
        data = json.load(f)

      # Convert old structure
      if isinstance(data, dict):
        data_list = []
        for file_id, item in data.items():
          if '/' in file_id:
            # If this is a path (rather than just a filename), update to use only the filename
            file_id = file_id.split('/')[-1]
          centre = item.pop('_centre')
          data_list.append({
              'centre': centre,
              'file_id': file_id,
              'scores': item,
          })
        data = data_list

      for item in data:
        result = Result.from_dict(item, config)
        self.results[result.file_id] = result

  def save(self) -> None:
    data = [result.to_dict() for result in self.results.values()]
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
      json.dump(data, temp_file, indent=2, ensure_ascii=False)
    os.replace(temp_file.name, self.path)

  def get_result(self, file_id: str) -> Result:
    if file_id not in self.results:
      self.results[file_id] = Result(
          file_id=file_id,
          scores={},
          taken=Result.parse_filename(file_id, self.config),
      )
    return self.results[file_id]
