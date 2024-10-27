import json
import pathlib

CURRENT_FOLDER = pathlib.Path(__file__).parent
IMAGE_FOLDER = CURRENT_FOLDER / 'images'
SCORE_FILE = CURRENT_FOLDER / 'scores.json'


def load_scores() -> dict:
  if SCORE_FILE.exists():
    with SCORE_FILE.open('r') as f:
      return json.load(f)
  else:
    return {}
