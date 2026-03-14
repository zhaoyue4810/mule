from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from app.core.yaml_loader import yaml_config
from app.schemas.admin_system import AdminYamlFileStatus, AdminYamlStatusResponse

router = APIRouter(tags=["admin-config"])


def _count_items(data: Any) -> int:
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in ("tests", "badges", "questions", "interaction_types", "categories"):
            value = data.get(key)
            if isinstance(value, (list, dict)):
                return len(value)
        return len(data)
    return 0


@router.get("/yaml-status", response_model=AdminYamlStatusResponse)
async def get_yaml_status() -> AdminYamlStatusResponse:
    yaml_config.ensure_loaded()
    files: list[AdminYamlFileStatus] = []
    for path in sorted(yaml_config.config_dir.rglob("*.yaml")):
        rel_path = str(path.relative_to(yaml_config.config_dir))
        try:
            payload = yaml_config._load_file(rel_path)  # noqa: SLF001
            mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            files.append(
                AdminYamlFileStatus(
                    file_name=rel_path,
                    status="ok",
                    item_count=_count_items(payload),
                    updated_at=mtime,
                )
            )
        except Exception:
            files.append(
                AdminYamlFileStatus(
                    file_name=rel_path,
                    status="error",
                    item_count=0,
                    updated_at=None,
                )
            )

    badge_definitions = {
        str(item.get("code")): item
        for item in yaml_config._store.get("badges", {}).get("badges", [])  # noqa: SLF001
        if isinstance(item, dict) and item.get("code")
    }
    return AdminYamlStatusResponse(
        files=files,
        summary=yaml_config.summary(),
        badge_definitions=badge_definitions,
    )


@router.post("/reload", response_model=AdminYamlStatusResponse)
async def reload_yaml() -> AdminYamlStatusResponse:
    yaml_config.reload()
    return await get_yaml_status()
