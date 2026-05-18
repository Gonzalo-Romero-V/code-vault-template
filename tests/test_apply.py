from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401
from lib.apply import apply_changes


def _silent(msg: str) -> None:
    pass


class ApplyTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name)
        (self.vault / "intent").mkdir()
        (self.vault / "domain").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel: str, content: str) -> Path:
        p = self.vault / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def test_create_action(self):
        payload = {"operations": [
            {"action": "create", "path": "domain/new.md",
             "content": "---\nstatus: draft\n---\n\n# New"}
        ]}
        c = apply_changes(payload, self.vault, ["locked"], _silent)
        self.assertEqual(c["applied"], 1)
        self.assertTrue((self.vault / "domain/new.md").exists())

    def test_create_idempotent_skips_existing(self):
        self._write("domain/exists.md", "---\nstatus: draft\n---\nbody")
        payload = {"operations": [
            {"action": "create", "path": "domain/exists.md", "content": "X"}
        ]}
        c = apply_changes(payload, self.vault, ["locked"], _silent)
        self.assertEqual(c["applied"], 0)
        self.assertEqual(c["skipped"], 1)

    def test_locked_guard_blocks_all_actions(self):
        self._write("intent/sys.md", "---\nstatus: locked\n---\nbody")
        for action in ("update_frontmatter", "append_section", "deprecate"):
            with self.subTest(action=action):
                payload = {"operations": [{
                    "action": action, "note": "intent/sys.md",
                    "set": {"status": "draft"},
                    "section": "X", "content": "x",
                }]}
                c = apply_changes(payload, self.vault, ["locked"], _silent)
                self.assertEqual(c["locked_blocked"], 1)
                self.assertEqual(c["applied"], 0)

    def test_update_frontmatter_idempotent(self):
        self._write("domain/x.md", "---\nstatus: draft\n---\nbody")
        payload = {"operations": [{
            "action": "update_frontmatter", "note": "domain/x.md",
            "set": {"status": "draft"},
        }]}
        c = apply_changes(payload, self.vault, ["locked"], _silent)
        self.assertEqual(c["skipped"], 1)
        self.assertEqual(c["applied"], 0)

    def test_update_frontmatter_preserves_yaml_list(self):
        self._write("domain/x.md",
                    "---\nstatus: draft\ntags:\n  - a\n  - b\n---\n\nbody")
        payload = {"operations": [{
            "action": "update_frontmatter", "note": "domain/x.md",
            "set": {"status": "stable"},
        }]}
        c = apply_changes(payload, self.vault, ["locked"], _silent)
        self.assertEqual(c["applied"], 1)
        text = (self.vault / "domain/x.md").read_text(encoding="utf-8")
        self.assertIn("status: stable", text)
        self.assertIn("- a", text)
        self.assertIn("- b", text)

    def test_append_section_creates_marker(self):
        self._write("domain/x.md", "---\nstatus: draft\n---\n\n# X\n")
        payload = {"operations": [{
            "action": "append_section", "note": "domain/x.md",
            "section": "Notes", "content": "Hello.",
        }]}
        c = apply_changes(payload, self.vault, ["locked"], _silent)
        self.assertEqual(c["applied"], 1)
        text = (self.vault / "domain/x.md").read_text(encoding="utf-8")
        self.assertIn("## Notes", text)
        self.assertIn("Hello.", text)

    def test_append_section_idempotent(self):
        initial = "---\nstatus: draft\n---\n\n# X\n\n## Notes\nHello.\n"
        self._write("domain/x.md", initial)
        payload = {"operations": [{
            "action": "append_section", "note": "domain/x.md",
            "section": "Notes", "content": "Hello.",
        }]}
        c = apply_changes(payload, self.vault, ["locked"], _silent)
        self.assertEqual(c["skipped"], 1)
        self.assertEqual(c["applied"], 0)

    def test_deprecate_action(self):
        self._write("domain/x.md", "---\nstatus: draft\n---\nbody")
        payload = {"operations": [
            {"action": "deprecate", "note": "domain/x.md"}
        ]}
        c = apply_changes(payload, self.vault, ["locked"], _silent)
        self.assertEqual(c["applied"], 1)
        text = (self.vault / "domain/x.md").read_text(encoding="utf-8")
        self.assertIn("status: deprecated", text)
        self.assertIn("deprecated_at:", text)

    def test_deprecate_idempotent(self):
        self._write("domain/x.md",
                    "---\nstatus: deprecated\ndeprecated_at: 2020-01-01\n---\nbody")
        payload = {"operations": [
            {"action": "deprecate", "note": "domain/x.md"}
        ]}
        c = apply_changes(payload, self.vault, ["locked"], _silent)
        self.assertEqual(c["skipped"], 1)

    def test_unknown_action_fails_loud_per_op(self):
        payload = {"operations": [
            {"action": "explode", "note": "domain/x.md"}
        ]}
        c = apply_changes(payload, self.vault, ["locked"], _silent)
        self.assertEqual(c["failed"], 1)

    def test_empty_payload(self):
        c = apply_changes({}, self.vault, ["locked"], _silent)
        self.assertEqual(c, {"applied": 0, "skipped": 0, "failed": 0, "locked_blocked": 0})


if __name__ == "__main__":
    unittest.main()
