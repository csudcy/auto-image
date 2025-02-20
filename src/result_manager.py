import dataclasses
import datetime
import json
import os
import pathlib
import re
import tempfile
from typing import Optional

import cachetools
from PIL import Image

from src.config import Config

# 2024-10-21 10.52.09-1.jpg
# skin-2018-07-18 12.59.08-2.jpg
# IMG_20240608_141605_1.jpg
DATETIME_RE = r'.*(\d{4}-?\d{2}-?\d{2}[ _]\d{2}.?\d{2}.?\d{2})'
# IMG-20161101-WA0000.jpg 
DATE_RE = r'.*(\d{4}-?\d{2}-?\d{2})'
DATETIME_FORMAT = '%Y%m%d %H%M%S'

IMAGE_CACHE = cachetools.LRUCache(maxsize=16)

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
  include_override: Optional[bool] = None
  lat_lon: Optional[LatLon] = None
  lat_lon_extracted: bool = False
  ocr_coverage: Optional[float] = None
  ocr_text: Optional[str] = None

  # Recalculated each time
  group_index: Optional[int] = None
  is_chosen: bool = False
  is_recent: bool = False
  location: Optional[str] = None
  path: Optional[pathlib.Path] = None
  taken: Optional[datetime.datetime] = None
  total: float = 0

  @property
  def image(self) -> Image.Image:
    if self.path:
      return load_image(self.path)
    else:
      raise Exception(f'Can\'t get image when path is not set! {self.file_id}')

  @classmethod
  def parse_filename(cls, file_id: str) -> Optional[datetime.datetime]:
    # Parse the datetime from the filename
    if match := re.match(DATETIME_RE, file_id):
      dt = match.group(1)
    elif match := re.match(DATE_RE, file_id):
      dt = f'{match.group(1)} 000000'
    else:
      print(f'  Unable to parse date: {file_id}')
      return None

    dt = dt.replace('-', '')
    dt = dt.replace('.', '')
    dt = dt.replace('_', ' ')
    return datetime.datetime.strptime(dt, DATETIME_FORMAT)

  @classmethod
  def from_dict(cls, data: dict) -> 'Result':
    file_id = data['file_id']
    if lat_lon_data := data.get('lat_lon'):
      lat_lon = LatLon(**lat_lon_data)
      lat_lon_extracted = True
    else:
      lat_lon = None
      lat_lon_extracted = data.get('lat_lon_extracted') or False
    return Result(
        centre=data.get('centre'),
        include_override=data.get('include_override'),
        file_id=data['file_id'],
        lat_lon_extracted=lat_lon_extracted,
        lat_lon=lat_lon,
        ocr_coverage=data.get('ocr_coverage'),
        ocr_text=data.get('ocr_text'),
        scores=data['scores'],
        taken=Result.parse_filename(file_id),
    )

  def to_dict(self) -> dict:
    if self.lat_lon:
      lat_lon = dataclasses.asdict(self.lat_lon)
    else:
      lat_lon = None
    return {
        'centre': self.centre,
        'include_override': self.include_override,
        'file_id': self.file_id,
        'lat_lon_extracted': self.lat_lon_extracted,
        'lat_lon': lat_lon,
        # Only save location name so we can see it in the JSON
        'location': self.location,
        'ocr_coverage': self.ocr_coverage,
        'ocr_text': self.ocr_text,
        'scores': self.scores,
    }

  def to_api_dict(self) -> dict:
    output = self.to_dict()
    if self.taken:
      taken = self.taken.isoformat()
    else:
      taken = None
    output.update({
        'taken': taken,
        'total': self.total,
        'group_index': self.group_index,
        'is_recent': self.is_recent,
        'is_chosen': self.is_chosen,
    })
    return output


@cachetools.cached(IMAGE_CACHE)
def load_image(path: pathlib.Path) -> Image.Image:
  return Image.open(path)


class ResultSet:

  def __init__(self, config: Config):
    self.config = config
    self.path = self.config.input_dir / '_auto_image.json'
    self.results: dict[Result] = {}
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
        result = Result.from_dict(item)
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
          taken=Result.parse_filename(file_id),
      )
    return self.results[file_id]
