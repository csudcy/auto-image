import collections
import json
import os
import pathlib
import statistics
import tempfile
import time

import jinja2

import score_clip

CURRENT_FOLDER = pathlib.Path(__file__).parent
IMAGE_FOLDER = CURRENT_FOLDER / 'images'
SCORE_FILE = CURRENT_FOLDER / 'scores-clip.json'
HTML_FILE = CURRENT_FOLDER / 'scores-clip.html'

# Check if anything can be identified (people, animals)
# Check for lots of text
# Check for skin/NSFW

TOTAL_KEY = '_total'
ORDER_BY = TOTAL_KEY

IMAGE_LIMIT = None

EXTENSIONS = ('jpg', 'png')

LABEL_SET = set(score_clip.LABELS)


def _load_scores() -> dict:
  if SCORE_FILE.exists():
    with SCORE_FILE.open('r') as f:
      return json.load(f)
  else:
    return {}


def _save_scores(scores: dict) -> None:
  with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
      json.dump(scores, temp_file, indent=2)
  os.replace(temp_file.name, SCORE_FILE)


def process() -> dict:
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

  print('Processing...')
  scores = _load_scores()
  next_time = overall.time
  for index, path in enumerate(IMAGE_FOLDER.rglob('*')):
    if IMAGE_LIMIT and index >= IMAGE_LIMIT:
      print('Hit limit; stopping...')
      break

    extension = path.suffix.lower().lstrip('.')
    if extension not in EXTENSIONS:
      print(f'  Skipping non-image: {path.name}')
      continue

    if time.perf_counter() >= next_time:
      _show_stats()
      _save_scores(scores)
      next_time = time.perf_counter() + 5

    # Check if the file has been scored already
    file_id = str(path.relative_to(IMAGE_FOLDER))

    # Process the scores
    if LABEL_SET.difference(scores.get(file_id) or {}):
      try:
        scores[file_id] = score_clip.get_score(path)
      except Exception as ex:
        print(f'  Error scoring {path.name} - {ex}')
      overall.processed += 1

  _show_stats()
  _save_scores(scores)

  print('Processing done!')

  return scores


def classify(scores: dict) -> None:
  for score in scores.values():
    score['_classifications'] = score_clip.classify(score)
    score[TOTAL_KEY] = sum(score['_classifications'])


def output_html(scores: dict) -> None:
  classify(scores)
  results = list(scores.items())
  results.sort(key=lambda result: result[1].get(ORDER_BY, -9999), reverse=True)

  # Calculate scorer stats
  stats = {}
  for scorer in score_clip.LABELS:
    single_scores = [
        score.get(scorer)
        for score in scores.values()
        if scorer in score
    ]
    stats[scorer] = {
        'min': min(single_scores),
        'mean': statistics.mean(single_scores),
        'median': statistics.median(single_scores),
        'max': max(single_scores),
    }
  
  # Calculate total stats
  total_counter = collections.Counter([
      round(score.get(TOTAL_KEY))
      for score in scores.values()
  ])

  print('Generating HTML...')
  env = jinja2.Environment(
      loader=jinja2.FileSystemLoader('templates'),
      autoescape=jinja2.select_autoescape()
  )
  template = env.get_template('output.tpl')
  html = template.render(
      scorers=score_clip.LABELS,
      stats=stats,
      results=results,
      total_counter=total_counter,
      path_prefix=IMAGE_FOLDER.relative_to(CURRENT_FOLDER),
  )

  print('Saving HTML...')
  with HTML_FILE.open('w') as f:
    f.write(html)

  print('HTML done!')


if __name__ == '__main__':
  scores = process()
  output_html(scores)
