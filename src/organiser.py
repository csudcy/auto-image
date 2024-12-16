import pathlib
import shutil
from typing import Optional

from PIL import Image
from PIL import ImageOps

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
      file_id: result
      for file_id, result in result_set.results.items()
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
        image = Image.open(result.path)
        if result.centre:
          centre = (result.centre[0] / image.size[0], result.centre[1] / image.size[1])
        else:
          centre = (0.5, 0.5)
        cropped = ImageOps.fit(image, crop_size, centering=centre)
        cropped.save(output_path, quality=95)
      else:
        shutil.copy(result.path, output_path)
      if index % 20 == 0:
        print(f'  Copied {index}...')
  else:
    print('Skipped applying file changes; use --apply to apply changes')

  print('Organising done!')
