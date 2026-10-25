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

    def test_count(self):
        run("init", cwd=self.dir)
        run("add", "a", cwd=self.dir)
        run("add", "b", cwd=self.dir)
        self.assertEqual(run("count", cwd=self.dir).stdout, "2\n")
