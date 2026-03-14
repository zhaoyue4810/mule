#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${SERVER_DIR}/.venv/bin/python"
CONDA_ENV_NAME="${CONDA_DEFAULT_ENV:-}"

if [[ -x "${VENV_PYTHON}" ]]; then
  cd "${SERVER_DIR}"
  exec "${VENV_PYTHON}" -m pytest "$@"
fi

if [[ -n "${CONDA_ENV_NAME}" ]] && command -v python >/dev/null 2>&1; then
  if python -c "import pytest" >/dev/null 2>&1; then
    cd "${SERVER_DIR}"
    exec python -m pytest "$@"
  fi
fi

echo "No usable Python test environment found." >&2
echo "Preferred option: virtualenv" >&2
echo "  cd ${SERVER_DIR}" >&2
echo "  python3 -m venv .venv" >&2
echo "  source .venv/bin/activate" >&2
echo "  pip install -e \".[dev]\"" >&2
echo "" >&2
echo "Conda option:" >&2
echo "  conda activate hjll_zy" >&2
echo "  cd ${SERVER_DIR}" >&2
echo "  python -m pip install -e \".[dev]\"" >&2
exit 1
