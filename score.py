import datetime
import pathlib

from src import html_generator
from src import result_manager
from src import score_processor

CURRENT_FOLDER = pathlib.Path(__file__).parent
IMAGE_FOLDER = CURRENT_FOLDER / 'images'

# IMAGE_FOLDER = pathlib.Path('/Users/csudcy/Library/CloudStorage/Dropbox/Camera Uploads')

# Copy chosen files to another directory
# Remove non-chosen files
# Check for very similar photos & choose the best one (before choosing top)
# Choose seasonal photos from previous years?

IMAGE_LIMIT = None

RECENT_DELTA = datetime.timedelta(weeks=56)
TOP_RECENT_COUNT = 200
TOP_OLD_COUNT = 100


if __name__ == '__main__':
  result_set = result_manager.ResultSet(IMAGE_FOLDER)
  scorer = score_processor.Scorer(IMAGE_FOLDER, result_set, image_limit=IMAGE_LIMIT)
  scorer.process()
  scorer.update_chosen(RECENT_DELTA, TOP_RECENT_COUNT, TOP_OLD_COUNT)
  html_generator.generate(result_set)
