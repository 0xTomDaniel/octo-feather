"""The integration tests' shared read-only fixture, prepared once per run (templates spec
#acceptance-shared-fixture): pytest-xdist's documented once-per-session pattern, a file lock
beside the run's shared temp dir, so the first worker prepares it and every other one reads it.
"""

import json
from pathlib import Path

import pytest
from filelock import FileLock

# Each name the app is fed, with the greeting it must print (a worked example, not computed).
GREETINGS = [{"name": "Ada", "text": "Hello, Ada"}, {"name": "Grace", "text": "Hello, Grace"}]


@pytest.fixture(scope="session")
def greetings(tmp_path_factory: pytest.TempPathFactory, worker_id: str) -> Path:
    """A read-only JSON file of GREETINGS; tests read it, never write it."""
    shared = tmp_path_factory.getbasetemp()
    if worker_id != "master":  # under xdist: the dir every worker of this run shares
        shared = shared.parent
    path = shared / "greetings.json"
    with FileLock(f"{path}.lock"):
        if not path.is_file():
            path.write_text(json.dumps(GREETINGS), encoding="utf-8")
            path.chmod(0o444)
            print(f"shared fixture greetings.json: prepared once for this run by {worker_id}")  # noqa: T201
    return path
