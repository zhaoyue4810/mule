#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${SERVER_DIR}/.venv/bin/python"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Missing virtualenv python: ${VENV_PYTHON}" >&2
  echo "Run the following once before asking me to execute backend tests:" >&2
  echo "  cd ${SERVER_DIR}" >&2
  echo "  python3 -m venv .venv" >&2
  echo "  source .venv/bin/activate" >&2
  echo "  pip install -e \".[dev]\"" >&2
  exit 1
fi

cd "${SERVER_DIR}"
exec "${VENV_PYTHON}" -m pytest "$@"
