# xince-server

FastAPI bootstrap service for XinCe.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

## Useful commands

```bash
bash scripts/run_pytest.sh
python ../scripts/yaml_validate.py
alembic upgrade head
```

## Stable test entry

To avoid PATH differences between shells, this project now provides a single backend test entry:

```bash
cd /Users/zhaoyue/pythonProject/mule/server
bash scripts/run_pytest.sh
```

If `.venv` or dev dependencies are missing, the script will print the exact setup commands needed.
