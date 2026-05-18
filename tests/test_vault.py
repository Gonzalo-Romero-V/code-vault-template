from __future__ import annotations
import unittest

from . import _bootstrap  # noqa: F401
from lib.vault import parse_frontmatter, update_frontmatter_text, is_protected


class TestParseFrontmatter(unittest.TestCase):

    def test_no_frontmatter_returns_empty_dict(self):
        fm, body = parse_frontmatter("hello world")
        self.assertEqual(fm, {})
        self.assertEqual(body, "hello world")

    def test_basic_key_value(self):
        fm, body = parse_frontmatter("---\nstatus: draft\nname: foo\n---\nbody")
        self.assertEqual(fm, {"status": "draft", "name": "foo"})
        self.assertEqual(body, "body")

    def test_unquotes_double_balanced(self):
        fm, _ = parse_frontmatter('---\ncode_path: ""\n---\nbody')
        self.assertEqual(fm["code_path"], "")

    def test_unquotes_single_balanced(self):
        fm, _ = parse_frontmatter("---\nname: 'foo bar'\n---\nbody")
        self.assertEqual(fm["name"], "foo bar")

    def test_does_not_unquote_unbalanced(self):
        fm, _ = parse_frontmatter("---\nname: \"foo'bar\"\n---\nbody")
        self.assertEqual(fm["name"], "foo'bar")  # outer dq, inner sq preserved

    def test_ignores_yaml_list_items_at_dict_level(self):
        # listas multilinea → la key existe con valor vacío, los items no
        # se interpretan en el dict plano.
        fm, _ = parse_frontmatter(
            "---\nstatus: draft\ntags:\n  - a\n  - b\nname: x\n---\nbody"
        )
        self.assertEqual(fm["tags"], "")
        self.assertEqual(fm["status"], "draft")
        self.assertEqual(fm["name"], "x")

    def test_ignores_comments(self):
        fm, _ = parse_frontmatter("---\n# header\nstatus: draft\n---\nbody")
        self.assertEqual(fm, {"status": "draft"})


class TestUpdateFrontmatterText(unittest.TestCase):

    def test_preserves_yaml_list_when_updating_other_key(self):
        before = (
            "---\nstatus: draft\ntags:\n  - a\n  - b\nname: x\n---\n\nbody\n"
        )
        after = update_frontmatter_text(before, {"status": "stable"})
        self.assertIn("status: stable", after)
        self.assertIn("- a", after)
        self.assertIn("- b", after)
        self.assertIn("name: x", after)
        self.assertIn("body", after)

    def test_replaces_yaml_list_with_single_value(self):
        before = "---\ntags:\n  - a\n  - b\nname: x\n---\n\nbody"
        after = update_frontmatter_text(before, {"tags": "single"})
        # La lista entera se reemplaza por la línea única.
        self.assertIn("tags: single", after)
        self.assertNotIn("- a", after)
        self.assertNotIn("- b", after)
        # Las demás keys sobreviven.
        self.assertIn("name: x", after)

    def test_adds_missing_key_at_end_of_frontmatter(self):
        before = "---\nstatus: draft\n---\n\nbody"
        after = update_frontmatter_text(before, {"code_path": "app/x.py"})
        self.assertIn("status: draft", after)
        self.assertIn("code_path: app/x.py", after)
        self.assertIn("body", after)

    def test_creates_frontmatter_when_missing(self):
        after = update_frontmatter_text("plain text", {"status": "draft"})
        self.assertTrue(after.startswith("---\nstatus: draft\n---"))
        self.assertIn("plain text", after)

    def test_preserves_quoted_value_when_not_touched(self):
        before = '---\nname: "hello world"\nstatus: draft\n---\nbody'
        after = update_frontmatter_text(before, {"status": "stable"})
        self.assertIn('name: "hello world"', after)


class TestIsProtected(unittest.TestCase):

    def test_locked_status_protected(self):
        note = {"frontmatter": {"status": "locked"}}
        self.assertTrue(is_protected(note, ["locked"]))

    def test_draft_not_protected(self):
        note = {"frontmatter": {"status": "draft"}}
        self.assertFalse(is_protected(note, ["locked"]))

    def test_case_insensitive(self):
        note = {"frontmatter": {"status": "LOCKED"}}
        self.assertTrue(is_protected(note, ["locked"]))


if __name__ == "__main__":
    unittest.main()
