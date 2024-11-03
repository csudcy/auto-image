import pathlib
import shutil

from src import result_manager


def process(
    result_set: result_manager.ResultSet,
    output_folder: pathlib.Path,
) -> None:
  print('Checking files...')
  # Find all files in the target folder
  existing_files = {
      file.name: file
      for file in output_folder.iterdir()
  }
  existing_file_set = set(existing_files.keys())

  # Get all chosen files
  chosen_files = {
      result.path.name: result.path
      for result in result_set.results.values()
      if result.is_chosen
  }
  chosen_file_set = set(chosen_files.keys())

  # Work out what files need to be added/removed
  files_to_add = chosen_file_set - existing_file_set
  files_to_remove = existing_file_set - chosen_file_set
  print(f'File operations: {len(files_to_add)} add, {len(files_to_remove)} remove')

  # Remove old files
  print(f'Removing {len(files_to_remove)} old files...')
  for index, filename in enumerate(files_to_remove):
    existing_files[filename].unlink()
    if index % 20 == 0:
      print(f'  Removed {index}...')
  
  # Copy new files
  print(f'Copying {len(files_to_add)} new files...')
  for index, filename in enumerate(files_to_add):
    output_path = output_folder / filename
    shutil.copy(chosen_files[filename], output_path)
    if index % 20 == 0:
      print(f'  Copied {index}...')

  print('Organising done!')
