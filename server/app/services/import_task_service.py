from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.importing import ImportTask
from app.models.test import Dimension, Option, Question, Test, TestPersona, TestVersion
from app.schemas.import_task import ImportTaskCreateRequest
from app.services.import_service import ImportService


class ImportTaskService:
    def __init__(self, db: AsyncSession, import_service: ImportService | None = None):
        self.db = db
        self.import_service = import_service or ImportService()

    async def create_task(self, payload: ImportTaskCreateRequest) -> ImportTask:
        file_path = Path(payload.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {payload.file_path}")

        task = ImportTask(
            file_type=payload.file_type,
            file_url=str(file_path),
            status="PENDING",
            operator_id=payload.operator_id,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_task(self, task_id: int) -> ImportTask | None:
        query = select(ImportTask).where(ImportTask.id == task_id)
        return await self.db.scalar(query)

    async def list_tasks(self) -> list[ImportTask]:
        query = select(ImportTask).order_by(ImportTask.id.desc())
        result = await self.db.scalars(query)
        return list(result)

    async def parse_task(self, task_id: int, force: bool = False) -> ImportTask:
        task = await self.get_task(task_id)
        if task is None:
            raise LookupError(f"Import task not found: {task_id}")

        if task.preview_json and not force:
            return task

        path = Path(task.file_url)
        if not path.exists():
            task.status = "FAILED"
            task.parse_log = f"File missing: {task.file_url}"
            await self.db.commit()
            await self.db.refresh(task)
            return task

        task.status = "PARSING"
        await self.db.commit()

        try:
            if task.file_type == "html":
                preview = self.import_service.parse_html_demo(path)
            elif task.file_type == "docx":
                preview = self.import_service.parse_docx_outline(path)
            else:
                raise ValueError(f"Unsupported file type: {task.file_type}")

            task.status = "PREVIEW"
            task.parse_log = "preview_generated"
            task.preview_json = {
                "file_type": preview.file_type,
                "title": preview.title,
                "summary": preview.summary,
                "draft": preview.draft,
                "warnings": preview.warnings,
            }
        except Exception as exc:
            task.status = "FAILED"
            task.parse_log = str(exc)

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def apply_task(self, task_id: int, note: str | None = None) -> ImportTask:
        task = await self.get_task(task_id)
        if task is None:
            raise LookupError(f"Import task not found: {task_id}")
        if task.status not in {"PREVIEW", "APPROVED"}:
            raise ValueError("Import task must be in PREVIEW before apply")
        if not task.preview_json:
            raise ValueError("Import task has no parsed preview")

        draft = task.preview_json.get("draft") or {}
        kind = draft.get("kind")

        if kind == "test_catalog":
            apply_result = await self._apply_test_catalog(task_id, draft)
        elif kind == "document_outline":
            apply_result = {
                "kind": kind,
                "applied": False,
                "reason": "document_outline drafts require manual content mapping",
            }
        else:
            raise ValueError(f"Unsupported draft kind: {kind}")

        preview_json = dict(task.preview_json)
        preview_json["apply_result"] = apply_result
        task.preview_json = preview_json
        task.status = "APPROVED"
        task.ai_log = note or "applied"

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def reject_task(self, task_id: int, reason: str | None = None) -> ImportTask:
        task = await self.get_task(task_id)
        if task is None:
            raise LookupError(f"Import task not found: {task_id}")
        task.status = "REJECTED"
        task.ai_log = reason or "rejected"
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def _apply_test_catalog(self, task_id: int, draft: dict) -> dict:
        created_tests = 0
        created_versions = 0
        updated_tests = 0

        for item in draft.get("tests", []):
            query = select(Test).where(Test.test_code == item["test_code"])
            test = await self.db.scalar(query)

            if test is None:
                test = Test(
                    test_code=item["test_code"],
                    title=item["name"],
                    category=item["category"],
                    is_match_enabled=bool(
                        item.get("is_match_enabled", item.get("is_match", False))
                    ),
                    participant_count=int(item.get("participant_count") or 0),
                    sort_order=int(item.get("sort_order") or 0),
                    yaml_source=f"import_task:{task_id}",
                )
                self.db.add(test)
                await self.db.flush()
                created_tests += 1
            else:
                test.title = item["name"]
                test.category = item["category"]
                test.is_match_enabled = bool(
                    item.get("is_match_enabled", item.get("is_match", False))
                )
                test.participant_count = int(item.get("participant_count") or 0)
                test.sort_order = int(item.get("sort_order") or 0)
                test.yaml_source = test.yaml_source or f"import_task:{task_id}"
                updated_tests += 1

            next_version = await self._next_import_version(test.id)
            version = TestVersion(
                test_id=test.id,
                version=next_version,
                status="IMPORTED_DRAFT",
                description=item.get("description") or f"Imported from task #{task_id}",
                duration_hint=item.get("duration_hint"),
                cover_gradient=item.get("cover_gradient"),
                report_template_code=item.get("report_template_code"),
            )
            self.db.add(version)
            await self.db.flush()
            await self._apply_structured_version_content(version.id, item)
            created_versions += 1

        return {
            "kind": "test_catalog",
            "applied": True,
            "created_tests": created_tests,
            "updated_tests": updated_tests,
            "created_versions": created_versions,
        }

    async def _next_import_version(self, test_id: int) -> int:
        query = select(func.max(TestVersion.version)).where(TestVersion.test_id == test_id)
        current = await self.db.scalar(query)
        return (current or 0) + 1

    async def _apply_structured_version_content(
        self,
        version_id: int,
        item: dict,
    ) -> None:
        for index, dimension in enumerate(item.get("dimensions") or [], start=1):
            self.db.add(
                Dimension(
                    version_id=version_id,
                    dim_code=dimension["dim_code"],
                    dim_name=dimension["dim_name"],
                    max_score=int(dimension.get("max_score") or 100),
                    sort_order=int(dimension.get("sort_order") or index),
                )
            )

        await self.db.flush()

        for question_data in item.get("questions") or []:
            question = Question(
                version_id=version_id,
                question_code=question_data.get("question_code"),
                seq=int(question_data["seq"]),
                question_text=question_data["question_text"],
                interaction_type=question_data["interaction_type"],
                emoji=question_data.get("emoji"),
                config=question_data.get("config"),
                dim_weights=question_data.get("dim_weights") or {},
            )
            self.db.add(question)
            await self.db.flush()

            for option_index, option_data in enumerate(
                question_data.get("options") or [],
                start=1,
            ):
                self.db.add(
                    Option(
                        question_id=question.id,
                        option_code=option_data.get("option_code"),
                        seq=int(option_data.get("seq") or option_index),
                        label=option_data["label"],
                        emoji=option_data.get("emoji"),
                        value=float(option_data.get("value") or 0),
                        score_rules=option_data.get("score_rules"),
                        ext_config=option_data.get("ext_config"),
                    )
                )

        for persona_data in item.get("personas") or []:
            self.db.add(
                TestPersona(
                    version_id=version_id,
                    persona_key=persona_data["persona_key"],
                    persona_name=persona_data["persona_name"],
                    emoji=persona_data.get("emoji"),
                    rarity_percent=persona_data.get("rarity_percent"),
                    description=persona_data.get("description"),
                    soul_signature=persona_data.get("soul_signature"),
                    keywords=persona_data.get("keywords") or [],
                    dim_pattern=persona_data.get("dim_pattern") or {},
                    capsule_prompt=persona_data.get("capsule_prompt"),
                )
            )

        await self.db.flush()
