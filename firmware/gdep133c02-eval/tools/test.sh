#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/host
cc -std=c11 -O2 -Wall -Wextra -Werror -fsanitize=address,undefined -Icomponents/epd \
  components/epd/frame.c components/epd/epd.c tests/test_core.c -o build/host/test_core
build/host/test_core assets/photo.epf
python3 -m unittest discover -s tests -p 'test_*.py'
