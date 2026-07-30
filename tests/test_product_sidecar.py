from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reviews_editorial.product_sidecar import (  # noqa: E402
    PRODUCT_CONTRACT,
    ProductPaths,
    ProductReviewsUiBridge,
    create_demo,
    initialize,
)


class ProductSidecarTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.paths = ProductPaths.from_values(
            root / "dados com acento edição",
            root / "Documentos" / "Reviews",
            root / "Documentos" / "Reviews" / "arquivo privado",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_initialize_creates_persistent_layout_and_registry(self) -> None:
        result = initialize(self.paths, actor="Editora Teste")
        self.assertTrue(result["initialized"])
        self.assertEqual(result["contract"], PRODUCT_CONTRACT)
        self.assertTrue(self.paths.database_path.is_file())
        self.assertTrue(self.paths.editions_root.is_dir())
        self.assertTrue(self.paths.config_path.is_file())
        self.assertFalse(result["runtime_manifest"]["private_corpus_included"])
        self.assertTrue(list(self.paths.backups_root.glob("*-initial.sqlite3")))

    def test_packaged_bridge_uses_external_documents_root(self) -> None:
        initialize(self.paths)
        bridge = ProductReviewsUiBridge(self.paths)
        info = bridge.dispatch("workspace-info")["data"]
        self.assertEqual(info["jobs_root"], str(self.paths.editions_root))
        self.assertEqual(info["database"], str(self.paths.database_path))
        self.assertTrue(bridge.dispatch("doctor")["data"]["passed"])
        bootstrap = bridge.dispatch("bootstrap")
        self.assertTrue(bootstrap["ok"])
        self.assertEqual(
            set(bootstrap["data"]),
            {
                "dashboard",
                "editions",
                "doctor",
                "validated_memory",
                "historical_memory",
                "lessons",
                "classifications",
                "drive_imports",
                "agent_runs",
            },
        )

    def test_demo_is_synthetic_and_separate(self) -> None:
        result = create_demo(self.paths)
        self.assertTrue(result["synthetic"])
        demo_db = Path(result["paths"]["database_path"])
        self.assertTrue(demo_db.is_file())
        self.assertNotEqual(demo_db, self.paths.database_path)

    def test_cli_has_version_without_product_paths(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "reviews_core.py"), "version"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["contract"], PRODUCT_CONTRACT)


if __name__ == "__main__":
    unittest.main()
