import argparse
import pathlib

from src import geocode_manager
from src import result_manager
from src import score_processor
from src import server
from src.config import Config


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
      '--output-count',
      type=int,
      default=100,
      help='Number of images to output (default: 100)',
  )
  parser.add_argument(
      '--apply',
      action='store_true',
      help='Copy the best files into output directory (default: False)',
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
  config = Config(
      input_dir=args.input_dir,
      output_dir=args.output_dir,
      max_images=args.max_images,
      minimum_score=args.minimum_score,
      output_count=args.output_count,
      crop_width=args.crop_width,
      crop_height=args.crop_height,
      latlng_precision=args.latlng_precision,
      tesser_path=args.tesser_path,
      ocr_coverage_threshold=args.ocr_coverage_threshold,
      ocr_text_threshold=args.ocr_text_threshold,
  )

  result_set = result_manager.ResultSet(config)
  if args.serve:
    server.serve(config, result_set)
  else:
    geocoder = geocode_manager.GeoCoder(config)
    scorer = score_processor.Scorer(config, result_set, geocoder)
    scorer.process()
    if args.apply:
      scorer.update_files()
    else:
      scorer.compare_files()
      config.log('Skipped applying file changes; use --apply to apply changes')


if __name__ == '__main__':
  main()
