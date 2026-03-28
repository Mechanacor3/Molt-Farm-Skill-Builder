from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm.operations import list_operations, load_operation


class OperationRegistryTests(unittest.TestCase):
    def test_load_operation_returns_manual_triage_definition(self) -> None:
        operation = load_operation("manual-triage")

        self.assertEqual("manual-triage", operation.name)
        self.assertEqual("triage-worker", operation.agent.name)
        self.assertEqual(["repo-triage"], operation.agent.skills)
        self.assertEqual(".", operation.inputs["target"])

    def test_list_operations_excludes_removed_manual_log_write(self) -> None:
        operation_names = [operation.name for operation in list_operations()]

        self.assertIn("manual-run-summary", operation_names)
        self.assertNotIn("manual-log-write", operation_names)

    def test_load_operation_raises_for_missing_name(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_operation("manual-log-write")


if __name__ == "__main__":
    unittest.main()
