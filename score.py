import collections
import datetime
import pathlib
import statistics

import jinja2

from src import result_manager
from src import score_processor

CURRENT_FOLDER = pathlib.Path(__file__).parent
IMAGE_FOLDER = CURRENT_FOLDER / 'images'
HTML_FILE = CURRENT_FOLDER / 'scores-clip-test.html'

# IMAGE_FOLDER = pathlib.Path('/Users/csudcy/Library/CloudStorage/Dropbox/Camera Uploads')
# HTML_FILE = CURRENT_FOLDER / 'scores-clip.html'

# Copy chosen files to another directory
# Remove non-chosen files
# Check for very similar photos & choose the best one (before choosing top)
# Choose seasonal photos from previous years?

IMAGE_LIMIT = None

RECENT_DELTA = datetime.timedelta(weeks=56)
TOP_RECENT_COUNT = 200
TOP_OLD_COUNT = 100


def _choose_top(results: list[result_manager.Result], count: int) -> None:
  results.sort(key=lambda result: result.total, reverse=True)
  for result in results[:count]:
    result.chosen = True


def classify(result_set: result_manager.ResultSet) -> None:
  now = datetime.datetime.now()
  recent_minimum = now - RECENT_DELTA
  recent_results = []
  old_results = []

  for result in result_set.results.values():
    result.is_recent = result.taken > recent_minimum
    if result.is_recent:
      recent_results.append(result)
    else:
      old_results.append(result)

  _choose_top(recent_results, TOP_RECENT_COUNT)
  _choose_top(old_results, TOP_OLD_COUNT)


def output_html(result_set: result_manager.ResultSet) -> None:
  results_list = list(result_set.results.values())
  results_list.sort(key=lambda result: result.total, reverse=True)

  # Calculate label stats
  stats = {}
  for label in score_processor.LABELS:
    label_scores = [
        result.scores[label]
        for result in result_set.results.values()
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
      for result in result_set.results.values()
  ])

  print('Generating HTML...')
  env = jinja2.Environment(
      loader=jinja2.FileSystemLoader('templates'),
      autoescape=jinja2.select_autoescape()
  )
  template = env.get_template('output.tpl')
  html = template.render(
      label_weights=score_processor.LABEL_WEIGHTS,
      total_weight=sum(score_processor.LABEL_WEIGHTS.values()),
      stats=stats,
      results=results_list,
      total_counter=total_counter,
  )

  print('Saving HTML...')
  with HTML_FILE.open('w') as f:
    f.write(html)

  print('HTML done!')


if __name__ == '__main__':
  result_set = result_manager.ResultSet(IMAGE_FOLDER)
  scorer = score_processor.Scorer(IMAGE_FOLDER, result_set, image_limit=IMAGE_LIMIT)
  scorer.process()
  classify(result_set)
  output_html(result_set)
