"""Which SCPR station this run works on, and everything that is specific to it.

One JSON file per station in SCPR-data-collection/stations/ (e.g. OO.AXCC1.json): network
and station code, the OOI reference designator (piweb file prefix), deployment date,
position, gauge coefficients, auxiliary-sensor conversions, calibration threshold, seafloor
density. Standard library only (the stand-alone scripts use it too).

The station is chosen with the SCPR_STATION environment variable or `--station` (scpr.py
sets the variable before importing the rest); default AXCC1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import json
import os
from pathlib import Path
import sys

STATIONS_DIR = Path(os.environ.get("SCPR_STATIONS_DIR") or Path(__file__).resolve().parent.parent / "stations")
DEFAULT = "AXCC1"


@dataclass
class Station:
    network: str
    station: str
    site: str
    status: str
    ref_des: str
    piweb_base: str
    deployed: date
    exclude_calibrations_before: date | None
    position: dict
    seafloor_density_kg_m3: float
    gravity_m_s2: float
    calibration_threshold_kpa: float | None          # None = "auto"
    planned_deployment: str | None
    gauges: dict
    auxiliary: dict
    notes: list = field(default_factory=list)

    @property
    def id(self) -> str:
        return f"{self.network}.{self.station}"

    @property
    def gauge_loc(self) -> dict[str, str]:
        return {g: v["location"] for g, v in self.gauges.items()}

    def aux(self, name: str) -> tuple[float, float] | None:
        v = self.auxiliary.get(name)
        return None if v is None else (float(v[0]), float(v[1]))

    def gauge_coefficients_known(self, gauge: str) -> bool:
        return all(self.gauges[gauge].get(k) is not None for k in ("U0", "Y1", "Y2", "Y3"))

    def describe(self) -> dict:
        """The block written into every drift_model.json: what the calibration file applies to."""
        return {"network": self.network, "station": self.station, "site": self.site,
                "ref_des": self.ref_des, "deployed": str(self.deployed),
                "position": self.position,
                "gauges": [{"gauge": g, "location": v["location"], "channel": "LDO", "serial": v.get("serial")}
                           for g, v in self.gauges.items()],
                "calibration_flag": {"location": "40", "channel": "LEF"}}


def _date(text):
    return None if text in (None, "") else date.fromisoformat(str(text)[:10])


def load(name: str | None = None) -> Station:
    """Station by code ("AXCC1") or id ("OO.AXCC1")."""
    name = (name or os.environ.get("SCPR_STATION") or DEFAULT).strip()
    matches = [p for p in STATIONS_DIR.glob("*.json") if p.stem == name or p.stem.split(".", 1)[-1] == name]
    if len(matches) != 1:
        known = ", ".join(sorted(p.stem for p in STATIONS_DIR.glob("*.json")))
        raise SystemExit(f"unknown SCPR station {name!r}; known: {known}")
    d = json.loads(matches[0].read_text())
    thr = d.get("calibration_threshold_kpa")
    return Station(network=d["network"], station=d["station"], site=d.get("site", ""), status=d.get("status", "active"),
                   ref_des=d["ref_des"], piweb_base=d.get("piweb_base", "http://piweb.ooirsn.uw.edu/scpr/data/"),
                   deployed=_date(d["deployed"]), exclude_calibrations_before=_date(d.get("exclude_calibrations_before")),
                   position=d.get("position", {}), seafloor_density_kg_m3=float(d.get("seafloor_density_kg_m3", 1030.0)),
                   gravity_m_s2=float(d.get("gravity_m_s2", 9.806)),
                   calibration_threshold_kpa=None if thr in (None, "auto") else float(thr),
                   planned_deployment=d.get("planned_deployment"),
                   gauges=d["gauges"], auxiliary=d.get("auxiliary", {}), notes=d.get("notes", []))


def all_stations(status: str | None = None) -> list[Station]:
    out = [load(p.stem) for p in sorted(STATIONS_DIR.glob("*.json"))]
    return [s for s in out if status is None or s.status == status]


def _take_station_argument() -> None:
    """`--station X` / `--station=X` on any command line selects the station; it is removed from
    sys.argv so the scripts' own argument parsers never see it."""
    argv = sys.argv
    for i, a in enumerate(argv[1:], 1):
        if a == "--station" and i + 1 < len(argv):
            os.environ["SCPR_STATION"] = argv[i + 1]
            del argv[i:i + 2]
            return
        if a.startswith("--station="):
            os.environ["SCPR_STATION"] = a.split("=", 1)[1]
            del argv[i]
            return


_take_station_argument()
CURRENT = load()
