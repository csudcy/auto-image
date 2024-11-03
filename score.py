import collections
from dataclasses import dataclass
import datetime
import json
import os
import pathlib
import re
import statistics
import tempfile
import time

import jinja2

import score_clip

CURRENT_FOLDER = pathlib.Path(__file__).parent
# IMAGE_FOLDER = CURRENT_FOLDER / 'images'
IMAGE_FOLDER = pathlib.Path('/Users/csudcy/Library/CloudStorage/Dropbox/Camera Uploads')
SCORE_FILE = CURRENT_FOLDER / 'scores-clip.json'
HTML_FILE = CURRENT_FOLDER / 'scores-clip.html'

# Copy chosen files to another directory
# Remove non-chosen files
# Check for very similar photos & choose the best one (before choosing top)
# Choose seasonal photos from previous years?

TOTAL_KEY = '_total'
ORDER_BY = TOTAL_KEY

IMAGE_LIMIT = None

EXTENSIONS = ('jpg', 'png')

LABEL_SET = set(score_clip.LABELS)

RECENT_DELTA = datetime.timedelta(weeks=56)
TOP_RECENT_COUNT = 200
TOP_OLD_COUNT = 100

# 2024-10-21 10.52.09-1.jpg
# skin-2018-07-18 12.59.08-2.jpg
DATETIME_RE = r'.*(\d{4}-\d{2}-\d{2} \d{2}.\d{2}.\d{2})'
DATETIME_FORMAT = '%Y-%m-%d %H.%M.%S'


@dataclass
class Result:
  path: str
  scores: dict[str, float]
  total: float = 0
  is_recent: bool = False
  is_chosen: bool = False


ResultsType = dict[str, Result]


def _load_results() -> ResultsType:
  if SCORE_FILE.exists():
    with SCORE_FILE.open('r') as f:
      scores = json.load(f)
    return {
        path: Result(path=path, scores=scores)
        for path, scores in scores.items()
    }
  else:
    return {}


def _save_results(results: ResultsType) -> None:
  scores = {
      path: result.scores
      for path, result in results.items()
  }
  with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
      json.dump(scores, temp_file, indent=2)
  os.replace(temp_file.name, SCORE_FILE)


def process() -> ResultsType:
  class StatTracker():
    processed: int = 0
    time: float = time.perf_counter()

  overall = StatTracker()
  last_stats = StatTracker()

  def _show_stats():
    new_time = time.perf_counter()

    diff_processed = overall.processed - last_stats.processed
    diff_time = new_time - last_stats.time
    if diff_processed and diff_time:
      processed_per_minute = diff_processed / (diff_time / 60)
    else:
      processed_per_minute = 0

    wall_time = new_time - overall.time
    print(f'Done {index} files (scored {overall.processed} in {wall_time:.01f}s, {processed_per_minute:.01f} per minute)')

    last_stats.processed = overall.processed
    last_stats.time = new_time

  print('Finding files...')
  results = _load_results()
  next_time = overall.time
  all_files = list(IMAGE_FOLDER.rglob('*'))
  file_count = len(all_files)

  print(f'Processing {file_count} files...')
  for index, path in enumerate(all_files):
    if IMAGE_LIMIT and index >= IMAGE_LIMIT:
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
      _show_stats()
      _save_results(results)
      next_time = time.perf_counter() + 5

    # Check if the file has been scored already
    file_id = str(path.relative_to(IMAGE_FOLDER))

    # Process the scores
    if file_id in results:
      process_now = bool(LABEL_SET.difference(results[file_id].scores))
    else:
      process_now = True
    if process_now:
      try:
        results[file_id] = Result(
            path=path,
            scores=score_clip.get_score(path),
        )
      except Exception as ex:
        print(f'  Error scoring {path.name} - {ex}')
      overall.processed += 1

  _show_stats()
  _save_results(results)

  print('Processing done!')

  return results


def _choose_top(results: list[Result], count: int) -> None:
  results.sort(key=lambda result: result.total, reverse=True)
  for result in results[:count]:
    result.chosen = True


def _parse_datetime(filename: str) -> datetime.datetime:
  match = re.match(DATETIME_RE, filename)
  if match:
    dt = match.group(1)
    return datetime.datetime.strptime(dt, DATETIME_FORMAT)
  else:
    print(f'  Unable to parse date: {filename}')
    return datetime.datetime.min


def classify(results: ResultsType) -> None:
  now = datetime.datetime.now()
  recent_minimum = now - RECENT_DELTA
  recent_results = []
  old_results = []

  for result in results.values():
    classification = score_clip.classify(result.scores)
    result.total = sum(classification)

    taken = _parse_datetime(result.path)
    result.is_recent = taken > recent_minimum
    if result.is_recent:
      recent_results.append(result)
    else:
      old_results.append(result)

  _choose_top(recent_results, TOP_RECENT_COUNT)
  _choose_top(old_results, TOP_OLD_COUNT)


def output_html(results: ResultsType) -> None:
  results_list = list(results.items())
  results_list.sort(key=lambda path_result: path_result[1].total, reverse=True)

  # Calculate label stats
  stats = {}
  for label in score_clip.LABELS:
    label_scores = [
        result.scores[label]
        for result in results.values()
        if label in result.scores
    ]
    stats[label] = {
        'min': min(label_scores),
        'mean': statistics.mean(label_scores),
        'median': statistics.median(label_scores),
        'max': max(label_scores),
    }
  
  # Calculate total stats
  total_counter = collections.Counter([
      round(result.total)
      for result in results.values()
  ])

  print('Generating HTML...')
  env = jinja2.Environment(
      loader=jinja2.FileSystemLoader('templates'),
      autoescape=jinja2.select_autoescape()
  )
  template = env.get_template('output.tpl')
  html = template.render(
      label_weights=score_clip.LABEL_WEIGHTS,
      total_weight=sum(score_clip.LABEL_WEIGHTS.values()),
      stats=stats,
      results=results_list,
      total_counter=total_counter,
      path_prefix=IMAGE_FOLDER.relative_to(CURRENT_FOLDER),
  )

  print('Saving HTML...')
  with HTML_FILE.open('w') as f:
    f.write(html)

  print('HTML done!')


if __name__ == '__main__':
  results = process()
  classify(results)
  output_html(results)
