#!/usr/bin/env bash
# Full refresh after a game patch: fetch sources, rebuild data, rebuild index.html.
set -euo pipefail
T="$(cd "$(dirname "$0")" && pwd)"
bash "$T/fetch_sources.sh"
python3 -I "$T/build_artifacts.py"
python3 -I "$T/build_data.py"
python3 -I "$T/build_site.py"
