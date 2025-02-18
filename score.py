import argparse
import datetime
import pathlib

from src import geocode_manager
from src import html_generator
from src import organiser
from src import result_manager
from src import score_processor
from src import server
from src.config import Config

# Copy chosen files to another directory
# Remove non-chosen files
# Check for very similar photos & choose the best one (before choosing top)
# Choose seasonal photos from previous years?
# Check if image will look good at specific zoom/crop


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
      '--minimum-score',
      type=float,
      default=-2,
      help='Minimum score for images to be used (default: -2)',
  )
  parser.add_argument(
      '--recent-days',
      type=int,
      default=400,
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
  parser.add_argument(
      '--apply',
      action='store_true',
      help='Copy the best files into output directory (default: False)',
  )
  parser.add_argument(
      '--crop',
      action='store_true',
      help='If set, crop the output image around the average of keypoints',
  )
  parser.add_argument(
      '--crop-width',
      type=int,
      default=1080,
      help='The width to crop images to',
  )
  parser.add_argument(
      '--crop-height',
      type=int,
      default=1920,
      help='The height to crop images to',
  )
  parser.add_argument(
      '--exclude-date',
      type=lambda s: datetime.datetime.strptime(s, '%Y%m%d').date(),
      action='append',
      dest='exclude_dates',
      help='Any dates which should be excluded from being output (YYYYMMDD)',
  )
  parser.add_argument(
      '--latlng-precision',
      type=int,
      default=4,
      help='Precision to use for lat-lng reverse geocoding (4dp ~= 10m accuracy)',
  )
  parser.add_argument(
      '--tesser-path',
      type=str,
      default='/usr/local/Cellar/tesseract/5.5.0/share/tessdata',
      help='Path to tesserdata folder of installed tesseract binary',
  )
  parser.add_argument(
      '--ocr-coverage-threshold',
      type=float,
      default=0.1,
      help='Images with OCR coverage above this threshold may be excluded',
  )
  parser.add_argument(
      '--ocr-text-threshold',
      type=int,
      default=100,
      help='Images with OCR text count above this threshold may be excluded',
  )
  parser.add_argument(
      '--serve',
      action='store_true',
      help='Whether to run the server (after doing everything else)',
  )

  args = parser.parse_args()
  recent_count = int(args.output_count * args.recent_percent / 100)
  old_count = args.output_count - recent_count
  config = Config(
      input_dir=args.input_dir,
      output_dir=args.output_dir,
      max_images=args.max_images,
      minimum_score=args.minimum_score,
      recent_delta=datetime.timedelta(days=args.recent_days),
      recent_count=recent_count,
      old_count=old_count,
      apply=args.apply,
      crop_size=(args.crop_width, args.crop_height) if args.crop else None,
      exclude_dates=args.exclude_dates or [],
      latlng_precision=args.latlng_precision,
      tesser_path=args.tesser_path,
      ocr_coverage_threshold=args.ocr_coverage_threshold,
      ocr_text_threshold=args.ocr_text_threshold,
  )

  result_set = result_manager.ResultSet(config)
  geocoder = geocode_manager.GeoCoder(config)
  scorer = score_processor.Scorer(config, result_set, geocoder)
  scorer.process()
  groups = scorer.find_groups()
  scorer.update_chosen()
  html_generator.generate(config, result_set, groups)
  organiser.process(config, result_set)
  if args.serve:
    server.serve(config, result_set, groups)


if __name__ == '__main__':
  main()
