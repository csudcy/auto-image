import argparse
import datetime
import pathlib

from src import html_generator
from src import organiser
from src import result_manager
from src import score_processor

# Copy chosen files to another directory
# Remove non-chosen files
# Check for very similar photos & choose the best one (before choosing top)
# Choose seasonal photos from previous years?


def main() -> None:
  parser = argparse.ArgumentParser(description='Process images from a directory.')
  parser.add_argument(
      'input_dir',
      type=pathlib.Path,
      help='Path to the input directory containing images.',
  )
  parser.add_argument(
      'output_dir',
      type=pathlib.Path,
      help='Path to the output directory for processed images.',
  )
  parser.add_argument(
      '--max-images',
      type=int,
      default=None,
      help='Maximum number of images to process (default: all)',
  )
  parser.add_argument(
      '--recent-days',
      type=int, default=400,
      help='Number of days to consider a file recent (default: 400)',
  )
  parser.add_argument(
      '--output-count',
      type=int,
      default=100,
      help='Number of images to output (default: 100)',
  )
  parser.add_argument(
      '--recent-percent',
      type=float,
      default=60,
      help='Percentage of output images to be recent (default: 60)',
  )
  args = parser.parse_args()

  recent_delta = datetime.timedelta(days=args.recent_days)
  recent_count = int(args.output_count * args.recent_percent / 100)
  old_count = args.output_count - recent_count

  result_set = result_manager.ResultSet(args.input_dir)
  scorer = score_processor.Scorer(result_set, image_limit=args.max_images)
  scorer.process()
  scorer.update_chosen(recent_delta, recent_count, old_count)
  html_generator.generate(result_set)
  organiser.process(result_set, args.output_dir)


if __name__ == '__main__':
  main()
