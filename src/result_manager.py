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

CENTRE_KEY = '_centre'

@dataclass
class Result:
  file_id: str
  scores: dict[str, dict[str, float]]
  taken: datetime.datetime

  path: Optional[pathlib.Path] = None
  centre: Optional[tuple[float, float]] = None
  total: float = 0
  group_index: Optional[int] = None
  is_recent: bool = False
  is_chosen: bool = False


class ResultSet:

  def __init__(self, image_folder: pathlib.Path):
    self.image_folder = image_folder
    self.path = image_folder / '_auto_image.json'
    self.results: dict[Result] = {}
    if self.path.exists():
      with self.path.open('r') as f:
        scores = json.load(f)
      for file_id, scores in scores.items():
        if '/' in file_id:
          # If this is a path (rather than just a filename), update to use only the filename
          file_id = file_id.split('/')[-1]
        result = self.get_result(file_id)
        if CENTRE_KEY in scores:
          result.centre = scores.pop(CENTRE_KEY)
        result.scores = scores

  def save(self) -> None:
    scores = {}
    for file_id, result in self.results.items():
      scores[file_id] = dict(**result.scores)
      scores[file_id][CENTRE_KEY] = result.centre
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        json.dump(scores, temp_file, indent=2)
    os.replace(temp_file.name, self.path)
  
  def get_result(self, file_id: str) -> Result:
    if file_id not in self.results:
      # Parse the datetime from the filename
      match = re.match(DATETIME_RE, file_id)
      if match:
        dt = match.group(1)
        dt = dt.replace('-', '')
        dt = dt.replace('.', '')
        dt = dt.replace('_', ' ')
        taken = datetime.datetime.strptime(dt, DATETIME_FORMAT)
      else:
        print(f'  Unable to parse date: {file_id}')
        taken = datetime.datetime.min

      self.results[file_id] = Result(
          file_id=file_id,
          scores={},
          taken=taken,
      )
    return self.results[file_id]
