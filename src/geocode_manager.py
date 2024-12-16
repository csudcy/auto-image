import dataclasses
from dataclasses import dataclass
import datetime
import json
import os
import pathlib
import re
import tempfile
import time
from typing import Any, Optional

from PIL import Image
from PIL import ExifTags
import requests

USER_AGENT = 'AutoImage; https://github.com/csudcy/auto-image'
HEADERS = {'User-Agent': USER_AGENT}
API = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}'

"""
https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=51.6369323728&lon=-0.500180780833

{
  "place_id": 21224025,
  "licence": "Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright",
  "osm_type": "way",
  "osm_id": 865509155,
  "lat": "51.63701097142857",
  "lon": "-0.5001133428571428",
  "category": "place",
  "type": "house",
  "place_rank": 30,
  "importance": 0.00000999999999995449,
  "addresstype": "place",
  "name": "",
  "display_name": "14, Mill Way, The Cedars Estate, Mill End, Maple Cross, Three Rivers, Hertfordshire, England, WD3 8QP, United Kingdom",
  "address": {
    "house_number": "14",
    "road": "Mill Way",
    "suburb": "The Cedars Estate",
    "village": "Maple Cross",
    "city": "Three Rivers",
    "county": "Hertfordshire",
    "ISO3166-2-lvl6": "GB-HRT",
    "state": "England",
    "ISO3166-2-lvl4": "GB-ENG",
    "postcode": "WD3 8QP",
    "country": "United Kingdom",
    "country_code": "gb"
  },
  "boundingbox": [
    "51.6369610",
    "51.6370610",
    "-0.5001633",
    "-0.5000633"
  ]
}
"""


@dataclass
class GeoCodeResult:
  lat: float
  lon: float
  data: dict

  @property
  def name(self) -> Optional[str]:
    # TODO: Work out what to display
    return self.data.get('name')


def _decode_coords(coords: tuple[Any, Any, Any], ref: str) -> float:
  # Coords may be PIL.TiffImagePlugin.IFDRational (but maybe other thingst too, not sure)
  decimal_degrees = float(coords[0]) + float(coords[1]) / 60 + float(coords[2]) / 3600
  if ref in ('N', 'E'):
    return decimal_degrees
  else:
    return -decimal_degrees


class GeoCoder:

  def __init__(self, image_folder: pathlib.Path):
    self.image_folder = image_folder
    self.path = image_folder / '_auto_image_geocoding.json'
    self.next_request = datetime.datetime.now()
    self.results: dict[GeoCodeResult] = {}
    if self.path.exists():
      with self.path.open('r') as f:
        data = json.load(f)
      for item in data:
        result = GeoCodeResult(**item)
        self.results[(result.lat, result.lon)] = result

  def save(self) -> None:
    data = [
        dataclasses.asdict(result)
        for result in self.results.values()
    ]
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        json.dump(data, temp_file, indent=2)
    os.replace(temp_file.name, self.path)

  def geocode_image(self, image_file: pathlib.Path) -> Optional[str]:
    # Extract the tags
    image = Image.open(image_file)
    exifdata = image.getexif()
    if not exifdata:
      return None

    # Get the geo data
    gpsinfo = exifdata.get_ifd(ExifTags.IFD.GPSInfo)
    if not gpsinfo or len(gpsinfo) < 6:
      return None
    
    # if len(gpsinfo) < 6:
    #   print('\n' * 5)
    #   print(gpsinfo)
    #   # print(f'{lat}, {lon}')
    #   import pdb; pdb.set_trace()

    # Decode the lat/lon
    lat = _decode_coords(gpsinfo[2], gpsinfo[1])
    lon = _decode_coords(gpsinfo[4], gpsinfo[3])

    # Return the geocoded name
    return self.get_result(lat, lon).name

  def get_result(self, lat: float, lon: float) -> GeoCodeResult:
    key = (lat, lon)
    if key not in self.results:
      # Make sure we're not making too many requests
      wait_time = (self.next_request - datetime.datetime.now()).total_seconds()
      if wait_time > 0:
        time.sleep(wait_time)

      url = API.format(lat=lat, lon=lon)
      response = requests.get(url, headers=HEADERS)
      response.raise_for_status()
      data = response.json()

      self.results[key] = GeoCodeResult(
          lat=lat,
          lon=lon,
          data=data,
      )
    return self.results[key]
