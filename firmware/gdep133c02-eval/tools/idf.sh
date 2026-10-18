#!/bin/bash
set -e
cd "$(dirname "$0")/.."
# Use the user's existing Espressif Installation Manager environment.
EVAL_IDF_ACTIVATE="${EVAL_IDF_ACTIVATE:-$HOME/.espressif/tools/activate_idf_v6.1.sh}"
if [ ! -f "$EVAL_IDF_ACTIVATE" ]; then
  echo 'Set EVAL_IDF_ACTIVATE to your installed ESP-IDF 6.1 activation script.' >&2
  exit 1
fi
# EIM provides a machine-readable environment; avoid changing IDE selection.
eval_environment="$(sh "$EVAL_IDF_ACTIVATE" -e)"
while IFS='=' read -r key value; do
  case "$key" in
    PATH) export PATH="$value:$PATH" ;;
    SYSTEM_PATH) ;;
    IDF_*|ESP_*|OPENOCD_SCRIPTS) export "$key=$value" ;;
  esac
done <<< "$eval_environment"
if [ "$(git -C "$IDF_PATH" rev-parse HEAD)" != fff9895c82d744c7237be8847347bdd1b07c6643 ]; then
  echo 'Wrong ESP-IDF commit; expected installed v6.1 fff9895c82d744c7237be8847347bdd1b07c6643' >&2
  exit 1
fi
exec python "$IDF_PATH/tools/idf.py" -B build/idf6.1 "$@"
