"""Simple manual test for download capture + processing + MongoDB update flow."""

import asyncio
import os
from datetime import datetime
from pathlib import Path


async def main() -> int:
    run_id = f"test-file-flow-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    downloads_dir = Path("artifacts") / "_test_downloads"
    artifacts_dir = Path("artifacts") / "_test_artifacts"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Make file paths configurable for local test without containers.
    os.environ["DOWNLOADS_DIR"] = str(downloads_dir.resolve())
    os.environ["ARTIFACTS_DIR"] = str(artifacts_dir.resolve())

    # Import after env setup so FileManager resolves directories correctly.
    from core.db import init_db
    from core.models.mongo_models import Run
    from core.services.file_manager import FileManager

    await init_db()

    run = Run(job_id="test-job", connector="test_connector", status="running", logs=["test run"])
    run.id = run_id
    await run.save()

    source_file = downloads_dir / "extrato_teste.xlsx"
    source_file.write_bytes(b"dummy-xlsx-content")

    metadata = {
        "bank": "Test Bank",
        "account": "123456",
        "date": datetime.now().strftime("%d%m%Y"),
    }

    original_paths = FileManager.capture_downloads(run_id=run_id, pattern="*.xlsx", timeout_seconds=3)
    if not original_paths:
        print("FAIL: capture_downloads did not find file")
        return 1

    files_metadata = []
    for idx, original_path in enumerate(original_paths, start=1):
        suffix = str(idx) if len(original_paths) > 1 else ""

        renamed_original = FileManager.rename_file(original_path, metadata, suffix=suffix) or original_path
        processed_path = FileManager.process_file(renamed_original, run_id, metadata, suffix=suffix)

        files_metadata.append(
            {
                "file_type": "original",
                "filename": Path(renamed_original).name,
                "path": FileManager.to_artifact_relative(renamed_original),
                "size_bytes": FileManager.get_file_size(renamed_original),
                "status": "ready",
            }
        )

        if processed_path:
            files_metadata.append(
                {
                    "file_type": "processed",
                    "filename": Path(processed_path).name,
                    "path": FileManager.to_artifact_relative(processed_path),
                    "size_bytes": FileManager.get_file_size(processed_path),
                    "status": "ready",
                }
            )

    await run.update({"$set": {"files": files_metadata, "status": "success"}})

    persisted = await Run.get(run_id)
    if not persisted or not persisted.files:
        print("FAIL: Run.files not persisted")
        return 1

    missing = []
    for file_meta in persisted.files:
        rel = file_meta.path if hasattr(file_meta, "path") else file_meta["path"]
        full_path = artifacts_dir / rel
        if not full_path.exists():
            missing.append(str(full_path))

    if missing:
        print("FAIL: Missing files on disk")
        for path in missing:
            print(f" - {path}")
        return 1

    print("PASS: file flow test completed")
    print(f"run_id={run_id}")
    print(f"files_saved={len(persisted.files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
