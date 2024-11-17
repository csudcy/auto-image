import pathlib
import shutil
import statistics

import jinja2

from src import result_manager
from src import score_processor

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates'),
    autoescape=jinja2.select_autoescape()
)

SCORES_PER_PAGE = 1000


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
  html_dir = result_set.image_folder / '_auto_image'
  if html_dir.exists():
    shutil.rmtree(html_dir)
  html_dir.mkdir()
  total_weight = sum(score_processor.LABEL_WEIGHTS.values())
  for index in range(0, len(results_list), SCORES_PER_PAGE):
    results_page = results_list[index:index+SCORES_PER_PAGE]
    index_min = index + 1
    index_max = index + len(results_page)
    _render_file(
        'scores.tpl',
        html_dir / f'scores_{index_min}_{index_max}.html',
        label_weights=score_processor.LABEL_WEIGHTS,
        total_weight=total_weight,
        stats=stats,
        index_min=index_min,
        index_max=index_max,
        results=results_page,
        minimum_score=minimum_score,
    )
  _render_file(
      'groups.tpl',
      html_dir / 'groups.html',
      groups=groups,
  )
  _render_file(
      'counts.tpl',
      html_dir / 'counts.html',
      score_stats=score_stats,
      total_stats=total_stats,
      minimum_score=minimum_score,
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
