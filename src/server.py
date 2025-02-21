from dataclasses import dataclass
from http import client
from io import BytesIO
import math
import os

import flask

from src import result_manager
from src.config import Config

# TODO:
# - Move result set save to a thread (quicker including/excluding, won't try to save twice at the same time)
# - Or move to sqlite?
# - More filtering:
#   - Date (range?)
#   - Score (range?)
#   - OCR text contains
#   - Include ovverride setting
#   - Location name includes
#   - ...
# - Sorting?
# - Allow process/apply from UI
# - Display (and set?) config through UI
# - Map view
# - Allow address to be overridden (per-image or per-latlng)
# - Allow crop to be changed
# - Re-generate cropped/captioned image if crop/address changes

INCLUDE_OVERRIDE_VALUES = {
    'true': True,
    'false': False,
    'none': None,
}


@dataclass
class Counts:
  total: int = 0
  chosen: int = 0


def serve(
    config: Config,
    result_set: result_manager.ResultSet,
) -> None:
  os.environ['FLASK_DEBUG'] = 'True'
  app = flask.Flask(__name__)

  @app.route('/')
  def index():
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
    try:
      page_index = int(flask.request.args.get('page_index'))
    except:
      page_index = 0
    try:
      page_size = int(flask.request.args.get('page_size'))
    except:
      page_size = 25
    chosen_only = ('chosen_only' in flask.request.args)

    results = sorted(result_set.results.values(), key=lambda result: result.taken)
    if chosen_only:
      results = [result for result in results if result.is_chosen]

    # Validate params
    total_results = len(results)
    total_pages = math.ceil(total_results / page_size)
    page_index = max(min(page_index, total_pages - 1), 0)

    # Filter/paginate results
    start_index = page_index * page_size
    end_index = start_index + page_size
    page = results[start_index:end_index]

    return flask.render_template(
        'grid.tpl',
        chosen_only=chosen_only,
        page_index=page_index,
        page_size=page_size,
        total_results=total_results,
        total_pages=total_pages,
        page=page,
        start_index=start_index,
        end_index=end_index,
    )

  @app.route('/result/<file_id>', methods=('GET', 'POST'))
  def result_handler(file_id: str):
    result = result_set.results.get(file_id)
    if result:
      if flask.request.method == 'POST':
        include_override = INCLUDE_OVERRIDE_VALUES[flask.request.form.get('include_override')]
        result.update_include_override(include_override)
        result_set.save()
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
        result
        for result in result_set.results.values()
        if result.group_index == group_index
    ]
    if results:
      if flask.request.method == 'POST':
        include_override = INCLUDE_OVERRIDE_VALUES[flask.request.form.get('include_override')]
        file_id = flask.request.form.get('file_id')
        for result in results:
          if file_id is None or file_id == result.file_id:
            result.update_include_override(include_override)
        result_set.save()
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

  app.run()
