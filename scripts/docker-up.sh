#!/usr/bin/env sh
set -eu

docker compose up --build -d
echo "Spider XHS Web is running at http://127.0.0.1:8000/"
