#!/bin/bash
cd "$(dirname "$0")"
PYTHONPATH="$(pwd)" .venv/bin/python spider/spider.py "$@"
