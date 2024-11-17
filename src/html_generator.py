import pathlib
import statistics

import jinja2

from src import result_manager
from src import score_processor

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates'),
    autoescape=jinja2.select_autoescape()
)


def generate(
    result_set: result_manager.ResultSet,
    groups: list[list[result_manager.Result]],
    minimum_score: float,
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
  score_stats = {}
  total_stats = {
      'count': 0,
      'recent_count': 0,
      'chosen_count': 0,
  }
  for result in result_set.results.values():
    total = round(result.total)
    if total not in score_stats:
      score_stats[total] = {
          'count': 0,
          'recent_count': 0,
          'chosen_count': 0,
      }
    score_stats[total]['count'] += 1
    total_stats['count'] += 1
    if result.is_recent:
      score_stats[total]['recent_count'] += 1
      total_stats['recent_count'] += 1
    if result.is_chosen:
      score_stats[total]['chosen_count'] += 1
      total_stats['chosen_count'] += 1

  print('Generating HTML...')
  _render_file(
      'scores.tpl',
      result_set.image_folder / '_auto_image_scores.html',
      label_weights=score_processor.LABEL_WEIGHTS,
      total_weight=sum(score_processor.LABEL_WEIGHTS.values()),
      stats=stats,
      results=results_list,
      minimum_score=minimum_score,
  )
  _render_file(
      'groups.tpl',
      result_set.image_folder / '_auto_image_groups.html',
      groups=groups,
  )
  _render_file(
      'counts.tpl',
      result_set.image_folder / '_auto_image_counts.html',
      score_stats=score_stats,
      total_stats=total_stats,
  )

  print('HTML done!')


def _render_file(
    template: str,
    output_path: pathlib.Path,
    **context
) -> None:
  template = JINJA_ENV.get_template(template)
  html = template.render(**context)
  with output_path.open('w') as f:
    f.write(html)
