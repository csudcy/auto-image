import json
import os
import pathlib
import statistics
import tempfile
import time

import jinja2

import score_blur
import score_exif_is_photo
import score_musiq
import score_vila

CURRENT_FOLDER = pathlib.Path(__file__).parent
IMAGE_FOLDER = CURRENT_FOLDER / 'images'
SCORE_FILE = CURRENT_FOLDER / 'scores.json'
HTML_FILE = CURRENT_FOLDER / 'scores.html'

# Check if anything can be identified by OpenCV?
SCORERS = (
    ('exif-is-photo', score_exif_is_photo.get_score),
    ('blur', score_blur.get_score),
    ('musiq', score_musiq.get_score),
    ('vila', score_vila.get_score),
)
SCORER_NAMES = [scorer for scorer, _ in SCORERS]
ORDER_BY = SCORER_NAMES[0]

IMAGE_LIMIT = None


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

    if time.perf_counter() >= next_time:
      _show_stats()
      _save_scores(scores)
      next_time = time.perf_counter() + 5

    # Check if the file has been scored already
    file_id = str(path.relative_to(IMAGE_FOLDER))
    file_scores = scores.get(file_id) or {}

    # Process the scores
    for name, score_func in SCORERS:
      # Check if this model has been done already
      if name in file_scores:
        continue
      
      file_scores[name] = score_func(path)
      overall.processed += 1

    # Save results back to scores
    scores[file_id] = file_scores

  _show_stats()
  _save_scores(scores)

  print('Processing done!')

  return scores


def output_html(scores: dict) -> None:
  results = list(scores.items())
  results.sort(key=lambda result: result[1][ORDER_BY], reverse=True)

  # Calculate stats
  stats = {}
  for scorer in SCORER_NAMES:
    single_scores = [
        score.get(scorer)
        for score in scores.values()
    ]
    stats[scorer] = {
        'min': min(single_scores),
        'mean': statistics.mean(single_scores),
        'median': statistics.median(single_scores),
        'max': max(single_scores),
    }

  print('Generating HTML...')
  env = jinja2.Environment(
      loader=jinja2.FileSystemLoader('templates'),
      autoescape=jinja2.select_autoescape()
  )
  template = env.get_template('output.tpl')
  html = template.render(
      scorers=SCORER_NAMES,
      stats=stats,
      results=results,
      path_prefix=IMAGE_FOLDER.relative_to(CURRENT_FOLDER),
  )

  print('Saving HTML...')
  with HTML_FILE.open('w') as f:
    f.write(html)

  print('HTML done!')


if __name__ == '__main__':
  scores = process()
  output_html(scores)
