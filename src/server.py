from http import client
from io import BytesIO
import math
import os

import flask

from src import result_manager
from src.config import Config

# TODO:
# - Change group page to use repeated result detail page?
# - Add more filtering:
#   - Date (range?)
#   - Score (range?)
#   - OCR text contains
#   - Include ovverride setting
#   - Location name includes
#   - ...
# - Allow process/apply from UI
# - Don't process when starting server
# - Allow address to be overridden (per-image or per-latlng)
# - Allow crop to be changed
# - Re-generate cropped/captioned image if crop/addres changes

INCLUDE_OVERRIDE_VALUES = {
    'true': True,
    'false': False,
    'none': None,
}


def serve(
    config: Config,
    result_set: result_manager.ResultSet,
    groups: list[list[result_manager.Result]],
) -> None:
  os.environ['FLASK_DEBUG'] = 'True'
  app = flask.Flask(__name__)

  @app.route('/')
  def index():
    return flask.render_template('index.tpl')

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
      return flask.render_template('result.tpl', result=result)
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
        for result in results:
          result.update_include_override(include_override)
        result_set.save()
      return flask.render_template('group.tpl', group_index=group_index, results=results)
    else:
      return flask.abort(client.NOT_FOUND)

  @app.route('/api/results')
  def results_handler():
    results = [result.to_api_dict() for result in result_set.results.values()]
    return flask.jsonify(results)

  @app.route('/image/<file_id>')
  def image_handler(file_id: str):
    result = result_set.results.get(file_id)
    if result and result.path:
      return flask.send_file(result.path)
    else:
      return flask.abort(client.NOT_FOUND)

  @app.route('/image/cropped/<file_id>')
  def image_cropped_handler(file_id: str):
    result = result_set.results.get(file_id)
    if result and result.path:
      cropped = result.get_cropped(config)
      img_io = BytesIO()
      cropped.save(img_io, 'JPEG', quality=config.output_quality)
      img_io.seek(0)
      return flask.send_file(img_io, mimetype='image/jpeg')
    else:
      return flask.abort(client.NOT_FOUND)

  app.run()
