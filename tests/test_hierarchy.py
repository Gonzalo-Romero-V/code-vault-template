from __future__ import annotations
import unittest

from . import _bootstrap  # noqa: F401 — añade scripts/ al sys.path
from lib.hierarchy import detect_layer, is_excluded, _match_any


class TestGlobMatching(unittest.TestCase):

    def test_recursive_double_star_at_end(self):
        self.assertTrue(_match_any("foo/bar/baz.py", ["foo/**"]))
        self.assertTrue(_match_any("foo", ["foo/**"]))  # bare dir match
        self.assertFalse(_match_any("fooz/bar.py", ["foo/**"]))

    def test_recursive_double_star_in_middle(self):
        # a/**/b debe matchear a/b, a/x/b, a/x/y/b, pero NO ab ni a/bz.
        self.assertTrue(_match_any("a/b", ["a/**/b"]))
        self.assertTrue(_match_any("a/x/b", ["a/**/b"]))
        self.assertTrue(_match_any("a/x/y/b", ["a/**/b"]))
        self.assertFalse(_match_any("ab", ["a/**/b"]))
        self.assertFalse(_match_any("a/bz", ["a/**/b"]))

    def test_recursive_double_star_at_start(self):
        # **/foo debe matchear foo, x/foo, x/y/foo.
        self.assertTrue(_match_any("foo", ["**/foo"]))
        self.assertTrue(_match_any("x/foo", ["**/foo"]))
        self.assertTrue(_match_any("x/y/foo", ["**/foo"]))
        self.assertFalse(_match_any("foobar", ["**/foo"]))

    def test_no_substring_false_positives(self):
        # Bug histórico: el fallback substring producía falsos positivos.
        # contests contiene "test" pero NO debe matchear **/test/**.
        self.assertFalse(_match_any("app/contests/runner.py", ["**/test/**"]))
        self.assertFalse(_match_any("attest/x.py", ["**/test/**"]))
        self.assertTrue(_match_any("app/test/runner.py", ["**/test/**"]))
        # Modelsabc no debe matchear Backend/app/Models/**.
        self.assertFalse(_match_any("Backend/app/Modelsabc/x.php",
                                    ["Backend/app/Models/**"]))
        self.assertTrue(_match_any("Backend/app/Models/User.php",
                                   ["Backend/app/Models/**"]))

    def test_wildcard_does_not_cross_slash(self):
        # * (un solo asterisco) NO cruza /
        self.assertTrue(_match_any("foo.py", ["*.py"]))
        self.assertFalse(_match_any("sub/foo.py", ["*.py"]))

    def test_normalization_backslash(self):
        # Paths Windows con \\ se normalizan a /
        self.assertTrue(_match_any("foo\\bar\\x.py", ["foo/**"]))


class TestDetectLayer(unittest.TestCase):

    def test_first_match_wins_in_declaration_order(self):
        # H4 antes que H5: components/ui/** debe ganar sobre components/**
        hm = {
            "H4_contracts": ["components/ui/**"],
            "H5_implementation": ["components/**"],
        }
        self.assertEqual(detect_layer("components/ui/button.tsx", hm), "H4_contracts")
        self.assertEqual(detect_layer("components/custom/foo.tsx", hm), "H5_implementation")

    def test_unclassified_when_no_match(self):
        hm = {"H4_contracts": ["app/models/**"]}
        self.assertEqual(detect_layer("random/file.txt", hm), "UNCLASSIFIED")


class TestExclude(unittest.TestCase):

    def test_node_modules(self):
        self.assertTrue(is_excluded("node_modules/x.js", ["**/node_modules/**"]))
        self.assertTrue(is_excluded("foo/node_modules/x.js", ["**/node_modules/**"]))
        self.assertFalse(is_excluded("foo/node-modules/x.js", ["**/node_modules/**"]))

    def test_lock_files(self):
        self.assertTrue(is_excluded("package-lock.json", ["**/*-lock.json"]))
        self.assertTrue(is_excluded("yarn.lock", ["**/*.lock"]))


if __name__ == "__main__":
    unittest.main()
