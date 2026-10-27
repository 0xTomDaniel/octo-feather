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
        run("add", "call mom", cwd=self.dir)
        # list numbers each note from 1, then a period and a space.
        self.assertEqual(run("list", cwd=self.dir).stdout, "1. buy milk\n2. call mom\n")
