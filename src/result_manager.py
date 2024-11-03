from dataclasses import dataclass
import datetime
import json
import os
import pathlib
import re
import tempfile

# 2024-10-21 10.52.09-1.jpg
# skin-2018-07-18 12.59.08-2.jpg
# IMG_20240608_141605_1.jpg
DATETIME_RE = r'.*(\d{4}-?\d{2}-?\d{2}[ _]\d{2}.?\d{2}.?\d{2})'
DATETIME_FORMAT = '%Y%m%d %H%M%S'


@dataclass
class Result:
  path: pathlib.Path
  file_id: str
  scores: dict[str, dict[str, float]]
  taken: datetime.datetime

  total: float = 0
  is_recent: bool = False
  is_chosen: bool = False


class ResultSet:

  def __init__(self, image_folder: pathlib.Path):
    self.image_folder = image_folder
    self.path = image_folder / '_auto_image.json'
    self.results = {}
    if self.path.exists():
      with self.path.open('r') as f:
        scores = json.load(f)
      for file_id, scores in scores.items():
        path = self.image_folder / file_id
        result = self.get_result(path)
        result.scores = scores

  def save(self) -> None:
    scores = {
        file_id: result.scores
        for file_id, result in self.results.items()
    }
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        json.dump(scores, temp_file, indent=2)
    os.replace(temp_file.name, self.path)
  
  def get_result(self, path: pathlib.Path) -> Result:
    file_id = str(path.relative_to(self.image_folder))
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
          path=path,
          file_id=file_id,
          scores={},
          taken=taken,
      )
    return self.results[file_id]
