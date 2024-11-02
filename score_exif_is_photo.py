import pathlib

from PIL import Image
from PIL import ExifTags

PHOTO_TAGS = (
    ExifTags.Base.BitsPerSample,
    ExifTags.Base.GPSInfo,
)


def get_score(image_path: pathlib.Path) -> float:
  image = Image.open(image_path)
  exifdata = image.getexif()
  if exifdata:
    for tag in PHOTO_TAGS:
      if tag in exifdata:
        return 1
    return -1
  else:
    return 0


def classify(score: float) -> int:
  if score == 1:
    # Definitely a photo
    return 1
  elif score == 0:
    # No exif data
    return 0
  else:
    # Not a photo
    return -100


if __name__ == '__main__':
  image_paths = (
      # Photo
      'images/2024-10-20 12.53.07.jpg',
      # Old photo
      'images/2019-02-09 20.09.45.jpg',
      'images/2020-03-17 07.59.02.jpg',
      # Screenshots
      # 'images/2024-10-20 20.14.29.jpg',
      # 'images/2024-10-20 20.14.22.jpg',
  )
  for image_path in image_paths:
    print(f'\n\n{image_path}\n')
    image = Image.open(image_path)
    exifdata = image.getexif()
    for tag_id in exifdata:
      # get the tag name, instead of human unreadable tag id
      tag = ExifTags.TAGS.get(tag_id, tag_id)
      data = exifdata.get(tag_id)
      # decode bytes 
      if isinstance(data, bytes):
        data = data.decode()
      print(f"{tag:25}: {data}")
