"""Where the SCPR pipeline reads and writes, for the current station (scpr_station.CURRENT).

Layout: <repo>/SCPR-data-collection/{bin, stations, calibration, timeseries, output, run}.
CALIBRATION and TIMESERIES are per station inside the git checkout (shared with users):
  calibration/OO.AXCC1/   calibrations.csv, calibration_days.csv, drift_model*.json, drift.png
  timeseries/OO.AXCC1/    scpr_pressure_hourly.csv, scpr_pressure.png, scpr_uplift.png
OUTPUT holds everything generated and large, one folder per station:
  <SCPR_OUTPUT>/OO.AXCC1/{raw, mseed, mseed_corrected, manifest, calibration, cache, logs}
SCPR_OUTPUT defaults to SCPR-data-collection/output, e.g. on the processing VM:
  export SCPR_OUTPUT=/data/scpr
"""

import os
from pathlib import Path

from scpr_station import CURRENT as STATION

BIN = Path(__file__).resolve().parent
ROOT = BIN.parent                         # SCPR-data-collection
CALIBRATION = ROOT / "calibration" / STATION.id
TIMESERIES = ROOT / "timeseries" / STATION.id
XML = ROOT / "output" / "xml"             # committed StationXML, OO_<STA>_<LOC>.xml
OUTPUT_ROOT = Path(os.environ.get("SCPR_OUTPUT") or ROOT / "output").expanduser().resolve()
OUTPUT = OUTPUT_ROOT / STATION.id

RAW = OUTPUT / "raw"                      # piweb .dat files, one folder per day
MSEED = OUTPUT / "mseed"                  # raw MiniSEED (quality D), SDS
CORRECTED = OUTPUT / "mseed_corrected"    # drift-corrected LDO (quality Q), SDS
MANIFEST = OUTPUT / "manifest"            # per-day JSON records
REPORT = OUTPUT / "calibration"           # per-run apply reports
CACHE = OUTPUT / "cache"                  # piweb file-size scan
LOGS = OUTPUT / "logs"
