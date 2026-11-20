import subprocess
import sys
import tempfile
import unittest


def run(body: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".md") as f:
        f.write(body)
        f.flush()
        return subprocess.run([sys.executable, "scripts/lane_tickets.py", f.name], capture_output=True, text=True, check=True).stdout.strip()


class LaneTickets(unittest.TestCase):
    def test_names(self) -> None:
        self.assertEqual(run("## Skills\n\nSkills: tdd, `eval-cases`\n"), "tdd, eval-cases")

    def test_none(self) -> None:
        self.assertEqual(run("## Skills\n\nSkills: none\n"), "none")
