import flask
import os

from src import result_manager
from src.config import Config


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

  app.run()
