import pathlib
import shutil
from typing import Optional

from PIL import Image

from src import result_manager


def process(
    result_set: result_manager.ResultSet,
    output_folder: pathlib.Path,
    apply: bool,
    crop_size: Optional[tuple[int, int]],
) -> None:
  print('Checking files...')
  # Find all files in the target folder
  output_folder.mkdir(parents=True, exist_ok=True)
  existing_files = {
      file.name: file
      for file in output_folder.iterdir()
  }
  existing_file_set = set(existing_files.keys())

  # Get all chosen files
  chosen_results = {
      result.path.name: result
      for result in result_set.results.values()
      if result.is_chosen
  }
  chosen_file_set = set(chosen_results.keys())

  # Work out what files need to be added/removed
  files_to_add = chosen_file_set - existing_file_set
  files_to_remove = existing_file_set - chosen_file_set
  print(f'File operations: {len(files_to_add)} add, {len(files_to_remove)} remove')

  if apply:
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
      output_path = output_folder / filename
      if crop_size:
        crop_width, crop_height = crop_size

        # Load the image
        image = Image.open(result.path)

        # Get the image size
        image_width, image_height = image.size

        # Find the size to extract
        ratio = min((
            image_width / crop_width,
            image_height / crop_height,
        ))
        image_crop_width = int(crop_width * ratio)
        image_crop_height = int(crop_height * ratio)

        space_width = image_width - image_crop_width
        space_height = image_height - image_crop_height
        assert (space_width == 0 and space_height >= 0) or (space_width >= 0 and space_height == 0)

        if result.centre:
          unbound_crop_left = result.centre[0] - int(image_crop_width / 2)
          crop_left = max(min(unbound_crop_left, space_width), 0)
          unbound_crop_top = result.centre[1] - int(image_crop_height / 2)
          crop_top = max(min(unbound_crop_top, space_height), 0)
        else:
          crop_left = int(space_width / 2)
          crop_top = int(space_height / 2)

        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        image_centre_x, image_centre_y = (int(image_width / 2), int(image_height / 2))
        space_width_half = int(space_width / 2)
        space_height_half = int(space_height / 2)
        draw.circle(
            (image_centre_x, image_centre_y),
            radius=25,
            fill=(255, 0, 0),
            outline=(255, 255, 255),
            width=5,
        )
        draw.rectangle(
            (space_width_half, space_height_half, space_width_half+image_crop_width, space_height_half+image_crop_height),
            outline=(255, 0, 0),
            width=5,
        )
        if result.centre:
          draw.circle(
              result.centre,
              radius=25,
              fill=(0, 0, 255),
              outline=(255, 255, 255),
              width=5,
          )
          draw.rectangle(
              (crop_left, crop_top, crop_left+image_crop_width, crop_top+image_crop_height),
              outline=(0, 0, 255),
              width=5,
          )
        image.save(output_path, quality=95)
      else:
        shutil.copy(result.path, output_path)
      if index % 20 == 0:
        print(f'  Copied {index}...')
  else:
    print('Skipped applying file changes; use --apply to apply changes')

  print('Organising done!')
