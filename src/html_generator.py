from dataclasses import dataclass
import pathlib
import shutil
import statistics

import jinja2

from src import result_manager
from src import score_processor
from src.config import Config

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates'),
    autoescape=jinja2.select_autoescape()
)

SCORES_PER_PAGE = 1000


@dataclass
class Counts:
  overall_total: int = 0
  overall_chosen: int = 0
  recent_total: int = 0
  recent_chosen: int = 0
  old_total: int = 0
  old_chosen: int = 0


def generate(
    config: Config,
    result_set: result_manager.ResultSet,
    groups: list[list[result_manager.Result]],
) -> None:
  results_list: list[result_manager.Result] = list(result_set.results.values())
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
  score_counts = {}
  total_counts = Counts()
  for result in result_set.results.values():
    total = round(result.total)
    if total not in score_counts:
      score_counts[total] = Counts()

    score_counts[total].overall_total += 1
    total_counts.overall_total += 1
    if result.is_chosen:
      score_counts[total].overall_chosen += 1
      total_counts.overall_chosen += 1

    if result.is_recent:
      score_counts[total].recent_total += 1
      total_counts.recent_total += 1
      if result.is_chosen:
        score_counts[total].recent_chosen += 1
        total_counts.recent_chosen += 1
    else:
      score_counts[total].old_total += 1
      total_counts.old_total += 1
      if result.is_chosen:
        score_counts[total].old_chosen += 1
        total_counts.old_chosen += 1

  print('Generating HTML...')
  html_dir = config.input_dir / '_auto_image'
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
        minimum_score=config.minimum_score,
    )
  _render_file(
      'groups.tpl',
      html_dir / 'groups.html',
      groups=groups,
  )
  _render_file(
      'counts.tpl',
      html_dir / 'counts.html',
      score_counts=score_counts,
      total_counts=total_counts,
      minimum_score=config.minimum_score,
  )

  results_with_ocr = [result for result in results_list if result.ocr_text]
  results_with_ocr.sort(key=lambda result: (len(result.ocr_text), result.ocr_coverage), reverse=True)
  for index in range(0, len(results_with_ocr), SCORES_PER_PAGE):
    results_page = results_with_ocr[index:index+SCORES_PER_PAGE]
    index_min = index + 1
    index_max = index + len(results_page)
    _render_file(
        'ocr.tpl',
        html_dir / f'ocr_{index_min}_{index_max}.html',
        index_min=index_min,
        index_max=index_max,
        results=results_page,
        ocr_coverage_threshold=config.ocr_coverage_threshold,
        ocr_text_threshold=config.ocr_text_threshold,
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
