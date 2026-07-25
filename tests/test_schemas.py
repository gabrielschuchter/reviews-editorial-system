from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SchemaTests(unittest.TestCase):
    def test_all_thirteen_schemas_are_valid_json_with_unique_ids(self) -> None:
        files = sorted((ROOT / "schemas").glob("*.schema.json"))
        self.assertEqual(len(files), 13)
        ids = []
        for path in files:
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema.get("additionalProperties", True))
            ids.append(schema["$id"])
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
