from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from dataclasses import field
import datetime
from enum import Enum
from http import client
from io import BytesIO
import math
import os
from typing import Callable, Optional

import flask
import pydantic

from src import result_manager
from src import score_processor
from src.config import Config

# TODO (functionality):
# - Allow crop to be changed
# - Allow all images to be updated en-masse (with filtering)
#  - Include/exclude
#  - Name
# - Force re-generate all exported images

# TODO (UI):
# - Apply filtering on all views & switch between display mode
#   - Grid (original)
#   - Grid (cropped)
#   - List
#   - Map
#   - Details? Need to deal with groups, what happens if you change filters, etc.
# - More filtering:
#   - Date quick filters (by month/year)
#   - OCR text empty, does not include
#   - Location name empty, does not include
# - Improve groups in grid:
#   - Group groups?
#   - Apply chosen/override setting to the group?
#   - Have separate group filters?

# TODO (Server):
# - Improve automation
#   - Rescan periodically
#   - Show a progress bar / counter
#   - Copy automatically
#   - Move logs onto a separate page (remove auto-refresh?)
# - Improve task queuing & tracking (list of tasks, progress bar per task, ...)
# - Make log check smarter (check more often for x time after a log was added)
# - Move to just a server?
#   - Pass in output directory
#   - Make source directories a list (default empty)
#   - Use default config for everything else
#   - Config needs to be editable through UI & saved somewhere
# - Move result set (& config) to sqlite?
#   - Generate thumbnails for all images & use in grid
#   - Generate cropped for all images (optionally use in grid?)
#   - Track tasks through db

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


class SortType(Enum):
  OCR_COVERAGE = 'ocr_coverage'
  TAKEN = 'taken'
  TOTAL = 'total'


SORT_KEYS = {
    SortType.OCR_COVERAGE:
        (lambda r: (r.ocr_coverage or 0, r.taken or datetime.datetime.min)),
    SortType.TAKEN: lambda r: r.taken or datetime.datetime.min,
    SortType.TOTAL: lambda r: (r.total or 0, r.taken or datetime.datetime.min),
}


class GridSettings(pydantic.BaseModel):
  chosen_yes: bool = False
  chosen_no: bool = False

  override_include: bool = False
  override_exclude: bool = False
  override_unset: bool = False

  date_from: datetime.date = datetime.date.min
  date_to: datetime.date = datetime.date.max

  score_from: float = -5.0
  score_to: float = 5.0

  location_name: Optional[str] = None

  ocr_coverage_from: Optional[float] = None
  ocr_coverage_to: Optional[float] = None

  ocr_text: Optional[str] = None

  north: Optional[float] = None
  south: Optional[float] = None
  east: Optional[float] = None
  west: Optional[float] = None

  page_index: int = 0
  page_size: int = 25

  sort_type: SortType = SortType.TAKEN
  sort_reverse: bool = True

  def get_matcher(self) -> Callable[[result_manager.Result], bool]:
    # - Chosen
    chosen_values = []
    if self.chosen_yes:
      chosen_values.append(True)
    if self.chosen_no:
      chosen_values.append(False)
    # - Override
    override_values = []
    if self.override_include:
      override_values.append(True)
    if self.override_exclude:
      override_values.append(False)
    if self.override_unset:
      override_values.append(None)
    # - Location
    location_name = self.location_name.lower() if self.location_name else None
    has_bounds = bool(self.north or self.south or self.east or self.west)
    # - OCR text
    ocr_text_lower = self.ocr_text.lower() if self.ocr_text else None

    def matcher(result: result_manager.Result) -> bool:
      return all((
          not chosen_values or result.is_chosen in chosen_values,
          not override_values or result.include_override in override_values,
          (not result.taken or
           self.date_from <= result.taken.date() <= self.date_to),
          result.total >= self.score_from and result.total <= self.score_to,
          not location_name or location_name in (result.location or '').lower(),
          not has_bounds or (result.lat_lon and all((
              self.north is None or self.north >= result.lat_lon.lat,
              self.south is None or self.south <= result.lat_lon.lat,
              self.east is None or self.east >= result.lat_lon.lon,
              self.west is None or self.west <= result.lat_lon.lon,
          ))),
          (self.ocr_coverage_from is None or
           (result.ocr_coverage or 0) >= self.ocr_coverage_from),
          (self.ocr_coverage_to is None or
           (result.ocr_coverage or 0) <= self.ocr_coverage_to),
          (not ocr_text_lower or
           ocr_text_lower in (result.ocr_text or '').lower()),
      ))

    return matcher


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
      'save': result_set.save,
  }

  action_executor = ThreadPoolExecutor(max_workers=1)

  @app.route('/', methods=('GET', 'POST'))
  def index():
    result: result_manager.Result
    count_chosen = len(
        [result for result in result_set.results.values() if result.is_chosen])

    return flask.render_template(
        'index.tpl',
        count_total=len(result_set.results),
        count_chosen=count_chosen,
    )

  def _process_action(action: str) -> None:
    if action_func := ACTION_FUNCS.get(action):
      try:
        action_func()
      except Exception as ex:
        config.log(f'Error running action {action}: {ex}')
    else:
      config.log(f'Unknown action: {action}')

  @app.route('/processing', methods=('GET', 'POST'))
  def processing():
    if flask.request.method == 'POST':
      action = flask.request.form.get('action')
      action_executor.submit(_process_action, action)

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
        'processing.tpl',
        total_counts=total_counts,
        group_count=len(group_indexes),
        grouped_counts=grouped_counts,
        ungrouped_counts=ungrouped_counts,
        score_counts=score_counts,
    )

  @app.route('/grid')
  def grid():
    # Process query params
    args_with_values = {
        arg: value for arg, value in flask.request.args.items() if value
    }
    settings = GridSettings(**args_with_values)

    # Work out date bounds & validate
    results = result_set.results.values()
    date_min = datetime.date.max
    date_max = datetime.date.min
    for result in results:
      if result.taken:
        result_date = result.taken.date()
        date_min = min(date_min, result_date)
        date_max = max(date_max, result_date)
    settings.date_from = min(max(settings.date_from, date_min), date_max)
    settings.date_to = min(max(settings.date_to, date_min), date_max)

    # Apply filters
    results = list(filter(settings.get_matcher(), results))

    # Validate Page index
    filtered_results = len(results)
    total_pages = math.ceil(filtered_results / settings.page_size)
    settings.page_index = max(min(settings.page_index, total_pages - 1), 0)

    # Sort
    results.sort(
        key=SORT_KEYS[settings.sort_type],
        reverse=settings.sort_reverse,
    )

    # Paginate results
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
        action = flask.request.form.get('action')
        if action == 'update_include_override':
          include_override = INCLUDE_OVERRIDE_VALUES[
              flask.request.form['include_override']]
          result.update_include_override(include_override)
        elif action == 'update_description':
          description = flask.request.form['description']
          result.update_description(description)
        else:
          raise Exception(f'Unknown action: {action}')
        action_executor.submit(_process_action, 'save')
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
        action = flask.request.form.get('action')
        if file_id := flask.request.form.get('file_id'):
          results_to_update = [result_set.results[file_id]]
        else:
          results_to_update = results
        if action == 'update_include_override':
          include_override = INCLUDE_OVERRIDE_VALUES[flask.request.form.get(
              'include_override')]
          for result in results_to_update:
            result.update_include_override(include_override)
        elif action == 'update_description':
          description = flask.request.form['description']
          for result in results_to_update:
            result.update_description(description)
        else:
          raise Exception(f'Unknown action: {action}')
        action_executor.submit(_process_action, 'save')
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
      return flask.send_file(img_io, mimetype='image/jpeg', max_age=0)
    else:
      return flask.abort(client.NOT_FOUND)

  @app.route('/api/logs/<int:min_index>')
  def api_logs(min_index: int):
    logs = config_logger.get_logs(min_index)
    return flask.jsonify(logs)

  @app.route('/map')
  def map():
    return flask.render_template('map.tpl',
                                 # results=results,
                                )

  @app.route('/api/map/points')
  def map_points():
    result: result_manager.Result
    points = [{
        'type': 'Feature',
        'properties': {
            'file_id': result.file_id,
            'group_index': result.group_index,
            'is_chosen': result.is_chosen,
            'location': result.location,
            'time_taken_text': result.get_time_taken_text(config),
        },
        'geometry': {
            'type': 'Point',
            'coordinates': [result.lat_lon.lon, result.lat_lon.lat],
        }
    } for result in result_set.results.values() if result.lat_lon]

    return flask.jsonify({'points': points})

  config.log('Server started!')
  app.run()
