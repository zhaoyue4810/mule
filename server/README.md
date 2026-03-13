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
pytest
python ../scripts/yaml_validate.py
alembic upgrade head
```
