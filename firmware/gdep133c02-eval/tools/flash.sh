#!/bin/bash
set -euo pipefail
if [ "$#" -ne 1 ]; then echo "Usage: $0 /dev/cu.usbserial-..." >&2; exit 1; fi
exec "$(dirname "$0")/idf.sh" -p "$1" -b 460800 flash monitor
