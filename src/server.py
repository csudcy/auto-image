from http import client
import os

import flask

from src import result_manager
from src.config import Config

# TODO:
# - Allow include/exclude from UI
# - Allow process/apply from UI
# - Don't process when starting server
# - Filtering (date range, number range, etc.)
# - Click group to see just that group
# - Only show top/chosen from group?
# - Compact view + detail popup/page

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

  app.run()
