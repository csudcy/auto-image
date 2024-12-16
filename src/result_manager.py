from dataclasses import dataclass
import datetime
import json
import os
import pathlib
import re
import tempfile
from typing import Optional

# 2024-10-21 10.52.09-1.jpg
# skin-2018-07-18 12.59.08-2.jpg
# IMG_20240608_141605_1.jpg
DATETIME_RE = r'.*(\d{4}-?\d{2}-?\d{2}[ _]\d{2}.?\d{2}.?\d{2})'
DATETIME_FORMAT = '%Y%m%d %H%M%S'

@dataclass
class Result:
  file_id: str
  scores: dict[str, dict[str, float]]
  taken: datetime.datetime

  path: Optional[pathlib.Path] = None
  centre: Optional[tuple[float, float]] = None
  location: Optional[str] = None
  total: float = 0
  group_index: Optional[int] = None
  is_recent: bool = False
  is_chosen: bool = False

  @classmethod
  def parse_filename(cls, file_id: str) -> datetime.datetime:
    # Parse the datetime from the filename
    match = re.match(DATETIME_RE, file_id)
    if match:
      dt = match.group(1)
      dt = dt.replace('-', '')
      dt = dt.replace('.', '')
      dt = dt.replace('_', ' ')
      return datetime.datetime.strptime(dt, DATETIME_FORMAT)
    else:
      print(f'  Unable to parse date: {file_id}')
      return datetime.datetime.min

  @classmethod
  def from_dict(cls, data: dict) -> 'Result':
    file_id = data['file_id']
    return Result(
        centre=data.get('centre'),
        file_id=data['file_id'],
        # TODO: Load location once we've worked out what bit of an address to show
        # location=data.get('location'),
        scores=data['scores'],
        taken=Result.parse_filename(file_id),
    )

  def to_dict(self) -> dict:
    return {
        'centre': self.centre,
        'file_id': self.file_id,
        'location': self.location,
        'scores': self.scores,
    }


class ResultSet:

  def __init__(self, image_folder: pathlib.Path):
    self.image_folder = image_folder
    self.path = image_folder / '_auto_image.json'
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
        json.dump(data, temp_file, indent=2)
    os.replace(temp_file.name, self.path)
  
  def get_result(self, file_id: str) -> Result:
    if file_id not in self.results:
      self.results[file_id] = Result(
          file_id=file_id,
          scores={},
          taken=Result.parse_filename(file_id),
      )
    return self.results[file_id]
