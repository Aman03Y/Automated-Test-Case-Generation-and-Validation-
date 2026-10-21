#!/usr/bin/env bash
# One-command dev launcher: backend :8000 + frontend :3000
# Usage: bun run dev   (recommended)  OR  ./start.sh  OR  bash start.sh
set -e
if ! command -v uv >/dev/null 2>&1; then echo "uv not found. Install: https://docs.astral.sh/uv/"; exit 1; fi
if ! command -v bun >/dev/null 2>&1; then echo "bun not found. Install: https://bun.sh"; exit 1; fi
# Prefer root concurrently launcher if available, else fallback
if [ -f package.json ] && grep -q '"dev"' package.json; then
  bun run dev
else
  uv run uvicorn backend.app:app --reload --port 8000 &
  API_PID=$!
  bun --cwd frontend run dev &
  WEB_PID=$!
  trap "kill $API_PID $WEB_PID 2>/dev/null; exit" INT TERM
  wait
fi
