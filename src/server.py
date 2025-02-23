from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from dataclasses import field
import datetime
from http import client
from io import BytesIO
import math
import os

import flask
import pydantic

from src import result_manager
from src import score_processor
from src.config import Config

# TODO:
# - Make log check smarter (check more often for x time after a log was added)
# - More filtering:
#   - Date (range?)
#   - OCR text empty, does not include
#   - Location name empty, does not include
# - Improve groups in grid:
#   - Group groups?
#   - Apply chosen/override setting to the group?
#   - Have separate group filters?
# - Sorting options - date, score, ocr coverage
# - Map view
# - Improve task queuing & tracking (list of tasks, progress bar per task, ...)
# - Move to just a server?
#   - Pass in output directory
#   - Make source directories a list (default empty)
#   - Use default config for everything else
#   - Config needs to be editable through UI & saved somewhere
# - Allow address to be overridden (per-image or per-latlng)
# - Allow crop to be changed
# - Re-generate cropped/captioned image if crop/address changes
# - Force re-generate all exported images
# - Move result set (& config) to sqlite?
# - Display (and set?) config through UI

INCLUDE_OVERRIDE_VALUES = {
    'true': True,
    'false': False,
    'none': None,
}


@dataclass
class Counts:
  total: int = 0
  chosen: int = 0


@dataclass
class Log:
  index: int
  now: datetime.datetime
  message: str


class GridSettings(pydantic.BaseModel):
  chosen_yes: bool = False
  chosen_no: bool = False

  override_include: bool = False
  override_exclude: bool = False
  override_unset: bool = False

  date_from: str = '2020-01-01'
  date_to: str = '2030-01-01'

  score_from: float = -5.0
  score_to: float = 5.0

  location_name: str = ''

  ocr_coverage_from: float = 0.0
  ocr_coverage_to: float = 1.0

  ocr_text: str = ''

  page_index: int = 0
  page_size: int = 25


@dataclass
class ConfigLogger:
  max_logs: int = 100
  next_index: int = 0
  logs: list[Log] = field(default_factory=list)

  def add_log(self, message: str) -> None:
    now = datetime.datetime.now()
    print(f'{now}: {message}')
    self.logs.append(Log(
        index=self.next_index,
        now=now,
        message=message,
    ))
    self.next_index += 1
    self.logs = self.logs[-self.max_logs:]

  def get_logs(self, min_index: int):
    logs = [{
        'now': log.now.strftime('%Y/%m/%d %H:%M:%S'),
        'message': log.message,
    } for log in self.logs if log.index >= min_index]
    return {
        'next_index': self.next_index,
        'logs': logs,
    }


def serve(
    config: Config,
    result_set: result_manager.ResultSet,
    scorer: score_processor.Scorer,
) -> None:
  os.environ['FLASK_DEBUG'] = 'True'
  app = flask.Flask(__name__)

  # Change logging to save here (and print)
  config_logger = ConfigLogger()
  config.log = config_logger.add_log

  ACTION_FUNCS = {
      'process': scorer.process,
      'check': scorer.compare_files,
      'apply': scorer.update_files,
  }

  action_executor = ThreadPoolExecutor(max_workers=1)

  @app.route('/', methods=('GET', 'POST'))
  def index():
    if flask.request.method == 'POST':
      action = flask.request.form.get('action')
      if action_func := ACTION_FUNCS.get(action):
        action_executor.submit(action_func)
      else:
        config.log(f'Unknown action: {action}')

    total_counts = Counts()
    group_indexes = set()
    grouped_counts = Counts()
    ungrouped_counts = Counts()
    score_counts = {}
    result: result_manager.Result
    for result in result_set.results.values():
      total = round(result.total)
      if total not in score_counts:
        score_counts[total] = Counts()

      score_counts[total].total += 1
      total_counts.total += 1
      if result.is_chosen:
        score_counts[total].chosen += 1
        total_counts.chosen += 1

      if result.group_index is None:
        ungrouped_counts.total += 1
        if result.is_chosen:
          ungrouped_counts.chosen += 1
      else:
        group_indexes.add(result.group_index)
        grouped_counts.total += 1
        if result.is_chosen:
          grouped_counts.chosen += 1

    return flask.render_template(
        'index.tpl',
        total_counts=total_counts,
        group_count=len(group_indexes),
        grouped_counts=grouped_counts,
        ungrouped_counts=ungrouped_counts,
        score_counts=score_counts,
    )

  @app.route('/grid')
  def grid():
    # Process query params
    settings = GridSettings(**flask.request.args)

    # Apply filters
    results = result_set.results.values()
    # - Chosen
    chosen_values = []
    if settings.chosen_yes:
      chosen_values.append(True)
    if settings.chosen_no:
      chosen_values.append(False)
    if chosen_values:
      results = [
          result for result in results if result.is_chosen in chosen_values
      ]
    # - Override
    override_values = []
    if settings.override_include:
      override_values.append(True)
    if settings.override_exclude:
      override_values.append(False)
    if settings.override_unset:
      override_values.append(None)
    if override_values:
      results = [
          result for result in results
          if result.include_override in override_values
      ]
    # - TODO: Date
    # - Score
    results = [
        result for result in results if (result.total >= settings.score_from and
                                         result.total <= settings.score_to)
    ]
    # - Location
    if settings.location_name:
      results = [
          result for result in results
          if result.location and settings.location_name in result.location
      ]
    # - OCR Coverage
    results = [
        result for result in results
        if ((result.ocr_coverage or 0) >= settings.ocr_coverage_from and
            (result.ocr_coverage or 0) <= settings.ocr_coverage_to)
    ]
    # - OCR text
    if settings.ocr_text:
      results = [
          result for result in results
          if (result.ocr_text and
              settings.ocr_text.lower() in result.ocr_text.lower())
      ]

    # Validate params
    filtered_results = len(results)
    total_pages = math.ceil(filtered_results / settings.page_size)
    settings.page_index = max(min(settings.page_index, total_pages - 1), 0)
    # TODO: Calculate date bounds & validate date_from/date_to
    date_min = '2020-01-01'
    date_max = '2030-01-01'

    # Sort
    results.sort(key=lambda result: result.taken)

    # Filter/paginate results
    start_index = settings.page_index * settings.page_size
    end_index = start_index + settings.page_size
    page = results[start_index:end_index]

    return flask.render_template(
        'grid.tpl',
        settings=settings,
        date_min=date_min,
        date_max=date_max,
        total_results=len(result_set.results),
        filtered_results=filtered_results,
        total_pages=total_pages,
        page=page,
    )

  @app.route('/result/<file_id>', methods=('GET', 'POST'))
  def result_handler(file_id: str):
    result = result_set.results.get(file_id)
    if result:
      if flask.request.method == 'POST':
        include_override = INCLUDE_OVERRIDE_VALUES[flask.request.form.get(
            'include_override')]
        result.update_include_override(include_override)
        action_executor.submit(result_set.save)
      return flask.render_template(
          'result.tpl',
          title=result.file_id,
          results=[result],
      )
    else:
      return flask.abort(client.NOT_FOUND)

  @app.route('/group/<int:group_index>', methods=('GET', 'POST'))
  def group_handler(group_index: int):
    results = [
        result for result in result_set.results.values()
        if result.group_index == group_index
    ]
    if results:
      if flask.request.method == 'POST':
        include_override = INCLUDE_OVERRIDE_VALUES[flask.request.form.get(
            'include_override')]
        file_id = flask.request.form.get('file_id')
        for result in results:
          if file_id is None or file_id == result.file_id:
            result.update_include_override(include_override)
        action_executor.submit(result_set.save)
      return flask.render_template(
          'result.tpl',
          title=f'Group {group_index}',
          results=results,
      )
    else:
      return flask.abort(client.NOT_FOUND)

  @app.route('/image/<file_id>')
  def image_handler(file_id: str):
    result = result_set.results.get(file_id)
    if result and result.path:
      return flask.send_file(result.path, max_age=600)
    else:
      return flask.abort(client.NOT_FOUND)

  @app.route('/image/cropped/<file_id>')
  def image_cropped_handler(file_id: str):
    result = result_set.results.get(file_id)
    if result and result.path:
      img_bytes = result.get_cropped_bytes(config)
      img_io = BytesIO()
      img_io.write(img_bytes)
      img_io.seek(0)
      return flask.send_file(img_io, mimetype='image/jpeg', max_age=600)
    else:
      return flask.abort(client.NOT_FOUND)

  @app.route('/api/logs/<int:min_index>')
  def api_logs(min_index: int):
    logs = config_logger.get_logs(min_index)
    return flask.jsonify(logs)

  config.log('Server started!')
  app.run()
