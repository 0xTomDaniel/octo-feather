import subprocess
import sys
import tempfile
import unittest


def run(*notes: str) -> str:
    paths = []
    for n in notes:
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
        f.write(n)
        f.close()
        paths.append(f.name)
    return subprocess.run([sys.executable, "scripts/lane_tickets.py", *paths], capture_output=True, text=True, check=True).stdout.strip()


class LaneTickets(unittest.TestCase):
    def test_names(self) -> None:
        self.assertEqual(run("## Skills\n\nSkills: tdd, `eval-cases`\n"), "tdd, eval-cases")

    def test_none(self) -> None:
        self.assertEqual(run("## Skills\n\nSkills: none\n"), "none")

    def test_comment_replaces_body(self) -> None:
        self.assertEqual(run("Skills: tdd\n", "Skills: eval-cases\n"), "eval-cases")
