import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

APP = pathlib.Path(__file__).resolve().parent.parent / "src" / "app.py"


def run(*args, cwd):
    return subprocess.run([sys.executable, str(APP), *args], cwd=cwd, capture_output=True, text=True)


class AppTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_add_then_list(self):
        run("init", cwd=self.dir)
        run("add", "buy milk", cwd=self.dir)
        self.assertEqual(run("list", cwd=self.dir).stdout, "buy milk\n")

    def test_missing_notes_names_the_fix(self):
        r = run("list", cwd=self.dir)
        self.assertEqual(r.returncode, 1)
        self.assertIn("run `app init`", r.stderr)

    def test_broken_notes_names_the_fix(self):
        pathlib.Path(self.dir, "notes.json").write_text("{")
        r = run("list", cwd=self.dir)
        self.assertEqual(r.returncode, 1)
        self.assertIn("run `app init`", r.stderr)

    def test_unknown_command_exits_2(self):
        # A usage error exits with status 2; every other error exits with status 1.
        r = run("frobnicate", cwd=self.dir)
        self.assertEqual(r.returncode, 2)
        self.assertIn("run `app init`, `app add \"<text>\"` or `app list`", r.stderr)

    def test_missing_argument_names_the_fix(self):
        r = run("add", cwd=self.dir)
        self.assertEqual(r.returncode, 2)
        self.assertIn("run `app add \"<text>\"`", r.stderr)
