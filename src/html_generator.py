import collections
import statistics

import jinja2

from src import result_manager
from src import score_processor


def generate(
    result_set: result_manager.ResultSet,
) -> None:
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
  path = result_set.image_folder / '_auto_image.html'
  with path.open('w') as f:
    f.write(html)

  print('HTML done!')
