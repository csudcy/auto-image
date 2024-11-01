import pathlib

import cv2
import numpy as np


def _score_blur_laplacian(image) -> float:
  gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  return cv2.Laplacian(gray_image, cv2.CV_64F).var()


def _score_blur_fft(image, size=60) -> float:
  # See https://pyimagesearch.com/2020/06/15/opencv-fast-fourier-transform-fft-for-blur-detection-in-images-and-video-streams/

  # Downsize the image for speed
  image = cv2.resize(image, (500, 500), interpolation=cv2.INTER_AREA)

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
  fftShift[cY - size:cY + size, cX - size:cX + size] = 0
  fftShift = np.fft.ifftshift(fftShift)
  recon = np.fft.ifft2(fftShift)

  # compute the magnitude spectrum of the reconstructed image,
  # then compute the mean of the magnitude values
  magnitude = 20 * np.log(np.abs(recon))
  mean = np.mean(magnitude)
  return mean


def get_score(image_path: pathlib.Path) -> float:
  # image_bytes = tf.constant(tf.io.read_file(str(image_path)))
  image = cv2.imread(image_path)
  gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

  # Check for blur
  # return _score_blur_laplacian(gray_image)
  return _score_blur_fft(gray_image)

  # Check if screenshot

  # Check if anything can be identified by OpenCV?

  return 0
