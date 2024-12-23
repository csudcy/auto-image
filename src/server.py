from flask import Flask

from src import result_manager
from src.config import Config


def serve(
    config: Config,
    result_set: result_manager.ResultSet,
    groups: list[list[result_manager.Result]],
) -> None:
  app = Flask(__name__)

  @app.route('/')
  def hello():
    return 'Hello, World!'

  app.run()
