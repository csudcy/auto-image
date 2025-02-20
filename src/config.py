import dataclasses
import pathlib
from typing import Optional

from PIL import ImageFont


@dataclasses.dataclass
class Config:
  input_dir: pathlib.Path
  output_dir: pathlib.Path
  max_images: Optional[int]
  minimum_score: float
  output_count: int
  apply: bool
  crop_width: int
  crop_height: int
  latlng_precision: int
  tesser_path: str
  ocr_coverage_threshold: float
  ocr_text_threshold: int

  # TODO: Add these to CLI?
  font_size: int = 50
  font_filename: str = 'Tahoma.ttf'
  text_offset_x: int = 20
  text_offset_y: int = -100
  font_colour: tuple[int, int, int] = (255, 255, 255)
  font_outline_width: int = 3
  font_outline_colour: tuple[int, int, int] = (0, 0, 0)
  taken_format: str = '%B, %Y'
  output_quality: int = 95

  @property
  def font(self) -> ImageFont:
    if not hasattr(self, '_font'):
      self._font = ImageFont.truetype(self.font_filename, self.font_size)
    return self._font
