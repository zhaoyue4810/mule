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
python scripts/check_runtime.py
```

## Stable test entry

To avoid PATH differences between shells, this project now provides a single backend test entry:

```bash
cd /Users/zhaoyue/pythonProject/mule/server
bash scripts/run_pytest.sh
```

If `.venv` or dev dependencies are missing, the script will print the exact setup commands needed.

If you use Conda instead of `venv`, that is also fine. For this project the currently usable environment can be:

```bash
conda activate hjll_zy
cd /Users/zhaoyue/pythonProject/mule/server
python -m pip install -e ".[dev]"
bash scripts/run_pytest.sh
```

`run_pytest.sh` will prefer `.venv`, but if no `.venv` exists it can fall back to the current Conda environment as long as `pytest` is installed there.

## Runtime check

Before deployment or when checking a new environment, you can run:

```bash
cd /Users/zhaoyue/pythonProject/mule/server
python scripts/check_runtime.py
```

It will print a JSON readiness report and exit with code `0` only when the service is ready to receive traffic.

For full release preparation, also follow:

- [/Users/zhaoyue/pythonProject/mule/docs/release-checklist.md](/Users/zhaoyue/pythonProject/mule/docs/release-checklist.md)
