import pathlib
import shutil
from typing import Optional

from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps

from src import result_manager
from src.config import Config


def process(
    config: Config,
    result_set: result_manager.ResultSet,
    # TODO: Move to CLI/config
    font_size: int = 50,
    font_filename: str = 'Tahoma.ttf',
    text_offset_x: int = 20,
    text_offset_y: int = -100,
    font_colour: tuple[int, int, int] = (255, 255, 255),
    font_outline_width: int = 3,
    font_outline_colour: tuple[int, int, int] = (0, 0, 0),
    taken_format: str = '%B, %Y',
) -> None:
  font = ImageFont.truetype(font_filename, font_size)
  outline_offsets = [
      (x_offset, y_offset)
      for x_offset in range(-font_outline_width, font_outline_width+1)
      for y_offset in range(-font_outline_width, font_outline_width+1)
      if (x_offset, y_offset) != (0, 0)
  ]

  print('Checking files...')
  # Find all files in the target folder
  config.output_dir.mkdir(parents=True, exist_ok=True)
  existing_files = {
      file.name: file
      for file in config.output_dir.iterdir()
  }
  existing_file_set = set(existing_files.keys())

  # Get all chosen files
  chosen_results = {
      file_id: result
      for file_id, result in result_set.results.items()
      if result.is_chosen
  }
  chosen_file_set = set(chosen_results.keys())

  # Work out what files need to be added/removed
  files_to_add = chosen_file_set - existing_file_set
  files_to_remove = existing_file_set - chosen_file_set
  print(f'File operations: {len(files_to_add)} add, {len(files_to_remove)} remove')

  if config.apply:
    # Remove old files
    print(f'Removing {len(files_to_remove)} old files...')
    for index, filename in enumerate(files_to_remove):
      existing_files[filename].unlink()
      if index % 20 == 0:
        print(f'  Removed {index}...')
    
    # Copy new files
    print(f'Copying {len(files_to_add)} new files...')
    for index, filename in enumerate(files_to_add):
      result = chosen_results[filename]
      output_path = config.output_dir / filename
      if config.crop_size:
        image_width, image_height = result.image.size
        if result.centre:
          centre = (result.centre[0] / image_width, result.centre[1] / image_height)
        else:
          centre = (0.5, 0.5)
        cropped = ImageOps.fit(result.image, config.crop_size, centering=centre)

        draw = ImageDraw.Draw(cropped)
        def _draw_text(x: int, y: int, text: str) -> None:
          # Outline
          for dx, dy in outline_offsets:
            draw.text((x + dx, y + dy), text, font_outline_colour, font=font)
          # Text
          draw.text((x, y), text, font_colour, font=font)

        # Add location
        text_top = config.crop_size[1] + text_offset_y
        if result.location:
          _draw_text(text_offset_x, text_top, result.location)
        if result.taken:
          taken_text = result.taken.strftime(taken_format)
          taken_size = int(draw.textlength(taken_text, font=font))
          taken_x = config.crop_size[0] - taken_size - 2 * text_offset_x
          _draw_text(taken_x, text_top, taken_text)

        cropped.save(output_path, quality=95)
      else:
        shutil.copy(result.path, output_path)
      if index % 20 == 0:
        print(f'  Copied {index}...')
  else:
    print('Skipped applying file changes; use --apply to apply changes')

  print('Organising done!')
