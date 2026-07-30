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

from reviews_editorial.ui_bridge import (  # noqa: E402
    BRIDGE_SCHEMA_VERSION,
    ReviewsUiBridge,
    UiBridgeError,
)


class ReviewsUiBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.bridge = ReviewsUiBridge(
            database_path=root / "registry.sqlite3",
            storage_root=root / "storage",
        )
        self.fixture = self.bridge.registry.seed_minimum_example(actor_id="fixture-editor")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_every_success_response_is_versioned(self) -> None:
        response = self.bridge.dispatch("list-editions")
        self.assertTrue(response["ok"])
        self.assertEqual(response["schema_version"], BRIDGE_SCHEMA_VERSION)
        self.assertEqual(response["errors"], [])
        self.assertIn("data", response)

    def test_list_and_inspect_edition_use_registry_data(self) -> None:
        listing = self.bridge.dispatch("list-editions")["data"]
        self.assertEqual(listing["total"], 1)
        edition_id = listing["items"][0]["edition_id"]
        inspected = self.bridge.dispatch(
            "inspect-edition", {"edition_id": edition_id}
        )["data"]
        self.assertEqual(inspected["edition"]["edition_id"], edition_id)
        self.assertGreaterEqual(len(inspected["documents"]), 1)
        self.assertGreaterEqual(len(inspected["versions"]), 1)
        self.assertGreaterEqual(len(inspected["timeline"]), 1)

    def test_memory_tiers_stay_separate(self) -> None:
        validated = self.bridge.dispatch(
            "search-memory", {"query": "", "tier": "validated"}
        )["data"]
        historical = self.bridge.dispatch(
            "search-memory", {"query": "", "tier": "historical"}
        )["data"]
        self.assertEqual(validated["memory_tier"], "validated")
        self.assertEqual(historical["memory_tier"], "historical")
        self.assertTrue(
            all(item["memory_tier"] == "validated" for item in validated["items"])
        )
        self.assertTrue(
            all(item["memory_tier"] == "historical" for item in historical["items"])
        )

    def test_compare_versions_registers_auditable_desktop_actor(self) -> None:
        compared = self.bridge.dispatch(
            "compare-versions",
            {
                "from_version_id": self.fixture["response_versions"][0],
                "to_version_id": self.fixture["response_versions"][1],
            },
        )
        self.assertTrue(compared["ok"])
        self.assertIn("version_diff_id", compared["data"])
        with self.bridge.registry.connection() as connection:
            actor = connection.execute(
                "SELECT role FROM actors WHERE actor_id='reviews-desktop'"
            ).fetchone()
        self.assertEqual(actor["role"], "editor")

    def test_unknown_commands_fail_with_structured_public_error(self) -> None:
        with self.assertRaises(UiBridgeError) as caught:
            self.bridge.dispatch("direct-sql")
        self.assertEqual(caught.exception.code, "COMMAND_NOT_ALLOWED")
        self.assertEqual(caught.exception.category, "usage_error")

    def test_cli_outputs_json_on_success_and_error(self) -> None:
        cli = ROOT / "scripts" / "reviews_ui_bridge.py"
        success = subprocess.run(
            [
                sys.executable,
                str(cli),
                "--db",
                str(self.bridge.registry.database_path),
                "--storage",
                str(self.bridge.registry.storage_root),
                "list-editions",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertTrue(json.loads(success.stdout)["ok"])

        failure = subprocess.run(
            [
                sys.executable,
                str(cli),
                "--db",
                str(self.bridge.registry.database_path),
                "--storage",
                str(self.bridge.registry.storage_root),
                "direct-sql",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(failure.returncode, 2, failure.stderr)
        payload = json.loads(failure.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["errors"][0]["code"], "COMMAND_NOT_ALLOWED")


if __name__ == "__main__":
    unittest.main()
