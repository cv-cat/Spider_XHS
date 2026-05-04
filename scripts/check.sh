#!/usr/bin/env sh
set -eu

if [ -x "./venv/bin/python" ]; then
  PYTHON="./venv/bin/python"
else
  PYTHON="python3"
fi

"$PYTHON" -m pytest
(cd frontend && npm run build)
