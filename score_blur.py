# Based on https://pyimagesearch.com/2020/06/15/opencv-fast-fourier-transform-fft-for-blur-detection-in-images-and-video-streams/

import pathlib

import cv2
import numpy as np

ZERO_SIZE = 60


def get_score(image_path: pathlib.Path) -> float:
  image = cv2.imread(image_path)

  # Downsize the image for speed
  image = cv2.resize(image, (500, 500), interpolation=cv2.INTER_AREA)

  # Make it grayscale
  image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

  # grab the dimensions of the image and use the dimensions to
  # derive the center (x, y)-coordinates
  (h, w) = image.shape
  (cX, cY) = (int(w / 2.0), int(h / 2.0))

  # compute the FFT to find the frequency transform, then shift
  # the zero frequency component (i.e., DC component located at
  # the top-left corner) to the center where it will be more
  # easy to analyze
  fft = np.fft.fft2(image)
  fftShift = np.fft.fftshift(fft)

  # zero-out the center of the FFT shift (i.e., remove low
  # frequencies), apply the inverse shift such that the DC
  # component once again becomes the top-left, and then apply
  # the inverse FFT
  fftShift[cY - ZERO_SIZE:cY + ZERO_SIZE, cX - ZERO_SIZE:cX + ZERO_SIZE] = 0
  fftShift = np.fft.ifftshift(fftShift)
  recon = np.fft.ifft2(fftShift)

  # compute the magnitude spectrum of the reconstructed image,
  # then compute the mean of the magnitude values
  magnitude = 20 * np.log(np.abs(recon))
  mean = np.mean(magnitude)
  return mean


def classify(score: float) -> int:
  if score <= 2:
    return -2
  elif score <= 12:
    return -1
  else:
    return 0
