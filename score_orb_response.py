# Based on https://www.opencvhelp.org/tutorials/image-analysis/feature-extraction/

import pathlib
import statistics

import cv2

ORB = None


def get_score(image_path: pathlib.Path) -> float:
  global ORB
  # Load the image
  image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

  # Create an ORB object
  if ORB is None:
    ORB = cv2.ORB_create()

  # Detect key points and compute descriptors
  key_points, _ = ORB.detectAndCompute(image, None)

  if key_points:
    return statistics.median((kp.response * 1000 for kp in key_points))
  else:
    return 0


def classify(score: float) -> int:
  if score <= 0.2:
    return -2
  elif score <= 0.3:
    return -1
  elif score <= 0.6:
    return 0
  else:
    return 1


if __name__ == '__main__':
  image_paths = (
      'images/2024-10-14 17.55.41.jpg',
      'images/2024-10-19 14.26.03.jpg',
      'images/2024-10-21 12.53.18.jpg',
      'images/2024-10-19 14.26.00.jpg',
  )

  # Create an ORB object
  orb = cv2.ORB_create()

  for image_path in image_paths:
    # Load the image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Detect key points and compute descriptors
    key_points, descriptors = orb.detectAndCompute(image, None)

    print(f'\n\n{image_path}')

    # print(len(key_points))
    # print(len(descriptors))

    # kp = key_points[0]
    # print(f'  {kp.angle=}')
    # print(f'  {kp.class_id=}')
    # print(f'  {kp.convert=}')
    # print(f'  {kp.octave=}')
    # print(f'  {kp.overlap=}')
    # print(f'  {kp.pt=}')
    # print(f'  {kp.response=}')
    # print(f'  {kp.size=}')

    attrs = ('class_id', 'response', 'size')
    for attr in attrs:
      attr_values = [getattr(kp, attr) * 1000 for kp in key_points]
      stats = {
          'min': min(attr_values),
          'mean': statistics.mean(attr_values),
          'median': statistics.median(attr_values),
          'max': max(attr_values),
      }
      print(f'{attr}: {stats}')

    # # Draw key points on the image
    # result = cv2.drawKeypoints(image, key_points, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    # # Display the result
    # cv2.imshow('ORB Features',result)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
