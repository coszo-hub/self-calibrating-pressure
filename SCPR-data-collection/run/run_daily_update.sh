#!/usr/bin/env bash
# Daily SCPR update for the processing VM (cron), for every active station (stations/*.json
# with "status": "active"; or SCPR_STATIONS="AXCC1 CZMID"). Per station: scans piweb for new days, adds any new
# calibration to calibration/calibrations.csv, refits the drift model, re-corrects every
# local day built with an older table/model, converts + corrects yesterday, rebuilds the
# hourly pressure time series and its figure (timeseries/), and pushes calibration/ and
# timeseries/ when they changed.
#
# Crontab (06:00 UTC):
#   0 6 * * * /path/to/self-calibrating-pressure/SCPR-data-collection/run/run_daily_update.sh
#
# Settings (environment, with defaults):
#   SCPR_OUTPUT   where raw/, mseed/, mseed_corrected/, manifest/, cache/ live
#   SCPR_PYTHON   python of the conda env from environment.yml
#   SCPR_PUSH     1 = commit and push calibration/ and timeseries/ when changed (needs git credentials)
#   SCPR_STATIONS stations to update (default: every station whose status is "active")
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"          # SCPR-data-collection
export SCPR_OUTPUT="${SCPR_OUTPUT:-$HERE/output}"
PYTHON="${SCPR_PYTHON:-$HOME/miniconda3/envs/scpr/bin/python}"
LOG_DIR="$SCPR_OUTPUT/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/update_$(date -u +%Y-%m-%d).log"

args=(update)
[ "${SCPR_PUSH:-1}" = "1" ] && args+=(--git-push)

cd "$HERE/bin" || exit 2
git -C "$HERE" pull --ff-only >>"$LOG" 2>&1 || echo "WARNING: git pull failed" >>"$LOG"
STATIONS="${SCPR_STATIONS:-$("$PYTHON" -c 'import json, glob; print(" ".join(d["station"] for d in map(lambda f: json.load(open(f)), sorted(glob.glob("../stations/*.json"))) if d.get("status") == "active"))')}"
status=0
for sta in $STATIONS; do
    echo "=== $sta $(date -u +%FT%TZ)" >>"$LOG"
    "$PYTHON" -u scpr.py --station "$sta" "${args[@]}" >>"$LOG" 2>&1 || status=$?
done
# Non-zero when a day could not be processed (e.g. piweb lines without timestamps that
# cannot be re-timed): cron mails the tail of the log so someone notices the same day.
if [ $status -ne 0 ]; then
    echo "scpr.py update exited with status $status for at least one station; see $LOG" >&2
    tail -20 "$LOG" >&2
fi
exit $status
