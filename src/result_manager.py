from dataclasses import dataclass
import datetime
import json
import os
import pathlib
import re
import tempfile

# 2024-10-21 10.52.09-1.jpg
# skin-2018-07-18 12.59.08-2.jpg
DATETIME_RE = r'.*(\d{4}-\d{2}-\d{2} \d{2}.\d{2}.\d{2})'
DATETIME_FORMAT = '%Y-%m-%d %H.%M.%S'


@dataclass
class Result:
  path: str
  scores: dict[str, dict[str, float]]
  total: float = 0
  is_recent: bool = False
  is_chosen: bool = False

  def parse_datetime(self) -> datetime.datetime:
    match = re.match(DATETIME_RE, self.path)
    if match:
      dt = match.group(1)
      return datetime.datetime.strptime(dt, DATETIME_FORMAT)
    else:
      print(f'  Unable to parse date: {self.path}')
      return datetime.datetime.min


class ResultSet:

  def __init__(self, path: pathlib.Path):
    self.path = path
    if self.path.exists():
      with self.path.open('r') as f:
        scores = json.load(f)
      self.results = {
          path: Result(path=path, scores=scores)
          for path, scores in scores.items()
      }
    else:
      self.results = {}

  def save(self) -> None:
    scores = {
        path: result.scores
        for path, result in self.results.items()
    }
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        json.dump(scores, temp_file, indent=2)
    os.replace(temp_file.name, self.path)
