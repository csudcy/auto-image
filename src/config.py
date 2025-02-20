import dataclasses
import datetime
import pathlib
from typing import Optional


@dataclasses.dataclass
class Config:
  input_dir: pathlib.Path
  output_dir: pathlib.Path
  max_images: Optional[int]
  minimum_score: float
  recent_delta: datetime.timedelta
  recent_count: int
  old_count: int
  apply: bool
  crop_size: Optional[tuple[int, int]]
  latlng_precision: int
  tesser_path: str
  ocr_coverage_threshold: float
  ocr_text_threshold: int
