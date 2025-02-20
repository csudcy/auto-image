from src import result_manager
from src.config import Config


def process(
    config: Config,
    result_set: result_manager.ResultSet,
) -> None:

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
      cropped = result.get_cropped(config)
      cropped.save(output_path, quality=95)
      if index % 20 == 0:
        print(f'  Copied {index}...')
  else:
    print('Skipped applying file changes; use --apply to apply changes')

  print('Organising done!')
