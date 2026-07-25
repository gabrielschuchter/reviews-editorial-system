from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.drive_policy import prepare_drive_transfer
from reviews_editorial.io import dump_data


class DrivePolicyTests(unittest.TestCase):
    def _job(self, root: Path, state: str = "candidate_for_review") -> tuple[Path, Path]:
        job_dir = root / "JOB-2026-001"
        candidate = job_dir / "final" / "candidate.docx"
        candidate.parent.mkdir(parents=True)
        candidate.write_bytes(b"candidate")
        dump_data(
            job_dir / "job.yml",
            {"job_id": "JOB-2026-001", "state": state},
        )
        return job_dir, candidate

    def _prepare(self, job_dir: Path, candidate: Path, destination: str = "production") -> dict:
        return prepare_drive_transfer(
            candidate,
            job_dir=job_dir,
            destination_folder_id=destination,
            authorized_production_folder_ids=["production"],
            source_archive_folder_ids=["source-archive"],
            job_id="JOB-2026-001",
            version="v01",
        )

    def test_only_authorized_candidate_is_prepared_without_upload(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            job_dir, candidate = self._job(Path(temp))
            manifest = self._prepare(job_dir, candidate)
            self.assertFalse(manifest["performed"])
            self.assertEqual(manifest["job_state"], "candidate_for_review")
            self.assertEqual(manifest["destination_folder_id"], "production")

    def test_candidate_outside_job_final_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            job_dir, _ = self._job(root)
            external = root / "candidate.docx"
            external.write_bytes(b"external")
            with self.assertRaises(PermissionError):
                self._prepare(job_dir, external)

    def test_unauthorized_or_source_destination_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            job_dir, candidate = self._job(Path(temp))
            with self.assertRaises(PermissionError):
                self._prepare(job_dir, candidate, destination="unknown")
            with self.assertRaises(PermissionError):
                prepare_drive_transfer(
                    candidate,
                    job_dir=job_dir,
                    destination_folder_id="source-archive",
                    authorized_production_folder_ids=["source-archive"],
                    source_archive_folder_ids=["source-archive"],
                    job_id="JOB-2026-001",
                    version="v01",
                )

    def test_early_job_state_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            job_dir, candidate = self._job(Path(temp), state="first_draft")
            with self.assertRaises(PermissionError):
                self._prepare(job_dir, candidate)


if __name__ == "__main__":
    unittest.main()
