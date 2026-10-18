#!/bin/bash
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null; then
  echo 'Install Python 3.10+ from https://www.python.org/downloads/macos/ then run again.'
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo 'Open Docker Desktop, wait until its engine is running, then run this script again.'
  exit 1
fi
if docker container inspect graph-practice >/dev/null 2>&1; then
  docker start graph-practice >/dev/null
elif docker container inspect ripple-db >/dev/null 2>&1; then
  docker start ripple-db >/dev/null
else
  docker run -d --name ripple-db -p 127.0.0.1:6379:6379 -p 127.0.0.1:3000:3000 -v ripple-data:/data falkordb/falkordb:latest --appendonly yes
fi
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; fi
printf '\nRipple is opening at http://localhost:5050 — keep this terminal open.\n'
# Read only the numeric PORT setting; never execute .env as shell code.
ripple_port=$(.venv/bin/python -c 'from dotenv import dotenv_values; print(int(dotenv_values(".env").get("PORT", "5050")))')
(sleep 3; open "http://localhost:$ripple_port") &
exec .venv/bin/python app.py
