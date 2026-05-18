from __future__ import annotations
import unittest

from . import _bootstrap  # noqa: F401
from lib.schema import validate_report, SCHEMA_VERSION


def _minimal_valid_report() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": "2026-01-01T00:00:00",
        "project_name": "Test",
        "commit": {"id": "abc", "message": "m", "branch": "main", "previous_id": ""},
        "scope": {"total_files": 0, "by_layer": {}, "size": "small"},
        "changes": [],
        "consistency": {"structural_checks": {"passed": [], "failed": [], "warnings": []}},
        "vault_hints": {"potentially_affected": [], "must_not_touch": []},
    }


class TestValidateReport(unittest.TestCase):

    def test_minimal_valid(self):
        self.assertEqual(validate_report(_minimal_valid_report()), [])

    def test_missing_top_level_key(self):
        r = _minimal_valid_report()
        del r["commit"]
        errs = validate_report(r)
        self.assertTrue(any("commit" in e for e in errs))

    def test_missing_nested_key(self):
        r = _minimal_valid_report()
        del r["commit"]["id"]
        errs = validate_report(r)
        self.assertTrue(any("commit.id" in e for e in errs))

    def test_wrong_type(self):
        r = _minimal_valid_report()
        r["scope"]["total_files"] = "5"  # should be int
        errs = validate_report(r)
        self.assertTrue(any("total_files" in e for e in errs))

    def test_schema_version_mismatch(self):
        r = _minimal_valid_report()
        r["schema_version"] = "9.9"
        errs = validate_report(r)
        self.assertTrue(any("schema_version" in e for e in errs))

    def test_invalid_change_type(self):
        r = _minimal_valid_report()
        r["changes"] = [{
            "path": "x.py", "type": "exploded", "layer": "H5_implementation",
            "lines_added": 0, "lines_removed": 0, "diff_excerpt": "",
        }]
        errs = validate_report(r)
        self.assertTrue(any("type invalid" in e for e in errs))

    def test_valid_change_type(self):
        r = _minimal_valid_report()
        r["changes"] = [{
            "path": "x.py", "type": "modified", "layer": "H5_implementation",
            "lines_added": 3, "lines_removed": 1, "diff_excerpt": "",
        }]
        self.assertEqual(validate_report(r), [])


if __name__ == "__main__":
    unittest.main()
