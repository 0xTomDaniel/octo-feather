"""Judgment-suite input validation through check-evals, no classifier execution.

The classifier ids, label set, calibration values and diagnostic literals are
inputs/oracles from tests/qa-judgment-shape.sh and tests/lib/qa.sh, not a
handcrafted provider recording. No classifier response is generated or replayed.
"""

from __future__ import annotations

import copy
import json
from testkit import Scratch, kit, main


class JudgmentInputs:
    """The legacy judgment shape fixture's JSON input documents in one scratch."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        self.root = s.root / "jg"
        (self.root / "jb" / "reference").mkdir(parents=True)
        (s.root / "evidence").mkdir()
        (s.root / "evidence" / "jb.md").write_text("bench\n")
        self.suite: dict[str, object] = {
            "suite": "jb", "kind": "judgment", "description": "judgment shape inputs",
            "timeout_s": 60,
        }
        self.cases: list[dict[str, object]] = [
            {"id": f"t{i}", "split": "train", "state": f"case t{i} PICK={pick}"}
            for i, pick in enumerate(["a"] * 5 + ["b"] * 5 + ["a"] * 2)
        ] + [
            {"id": f"h{i}", "split": "held-out", "state": f"case h{i} PICK=a"}
            for i in range(3)
        ]
        labels = ["a"] * 6 + ["b"] * 6 + ["a", "b", "b"]
        self.expectations: dict[str, dict[str, object]] = {
            str(c["id"]): {"label": label, "reason": f"SECRET-REASON {c['id']}",
                           "source": "tests/qa.sh"}
            for c, label in zip(self.cases, labels, strict=True)
        }
        self.model: dict[str, object] = {"model": "stub/first", "evidence": "evidence/jb.md"}
        self.pinned = {
            f"stub/{i}": "r" for i in (
                "token", "first", "broken", "cheap-train", "p/q-1.2", "p/q-latest",
                "yesno", "m-current",
            )
        }
        self.yesno: dict[str, object] = {
            "ruling": "stub yes/no ruling", "error": "stub bool only (400)", "evidence": "stub run",
        }
        self.catalogue: dict[str, object] = {
            "owner": "stub ruling, tests/qa.sh",
            "moving_alias": ["stub/~x/y", "stub/x-latest:free", "stub/p/q-1.2:free"],
            "yes_no_only": {"stub/ynr": self.yesno}, "pinned": self.pinned,
        }
        self.files: dict[str, object] = {
            "jb/suite.json": self.suite, "jb/cases.json": self.cases,
            "jb/reference/expectations.json": self.expectations,
            "jb/question.json": {"id": "q-ab", "question": "Is it a or b?", "labels": ["a", "b"],
                                 "label_help": {"a": "an a", "b": "a b"}, "state_shape": "a token"},
            "judgment-model.json": self.model, "classifiers.json": self.catalogue,
        }
        self.write(self.files)

    def write(self, files: dict[str, object]) -> None:
        for name, value in files.items():
            (self.root / name).write_text(json.dumps(value))

    def check(self, expected: str | None = None) -> None:
        got = self.s.run([kit("check-evals"), str(self.root)], want=1 if expected else 0)
        if expected:
            assert expected in got.out + got.err, got

    def changed(self, name: str, value: object, expected: str | None) -> None:
        """One input document replaced; every other document remains pristine."""
        self.write(self.files)
        (self.root / name).write_text(json.dumps(value))
        self.check(expected)

    def missing(self, name: str, expected: str) -> None:
        self.write(self.files)
        (self.root / name).unlink()
        self.check(expected)


def labels_shape(s: Scratch) -> None:
    """All original judgment label, split, minimum-set and labeller oracles."""
    q = JudgmentInputs(s)
    q.check()
    changes: list[tuple[str, object, str]] = [
        ("reason", None, "field reason: missing"),
        ("source", None, "field source: missing"),
        ("label", "c", "field label: must be one of ['a', 'b'], got 'c'"),
        ("reason", "two\nlines", "field reason: must be one non-empty line"),
        ("labelled_by", " ", "field labelled_by: must be one non-empty line"),
        ("relabel", "two\nlines", "field relabel: must be one non-empty line"),
        ("note", "x", "field note: unknown field"),
    ]
    for field, value, expected in changes:
        e = copy.deepcopy(q.expectations)
        if value is None:
            del e["t3"][field]
        else:
            e["t3"][field] = value
        q.changed("jb/reference/expectations.json", e,
                  "jb/reference/expectations.json case t3: " + expected)
    e = copy.deepcopy(q.expectations)
    e["t3"].update(labelled_by="director", relabel="was b")
    q.changed("jb/reference/expectations.json", e, None)
    c = copy.deepcopy(q.cases)
    del c[2]["split"]
    q.changed("jb/cases.json", c, "jb/cases.json case t2: field split: missing")
    c = copy.deepcopy(q.cases)
    c[2]["label"] = "a"
    q.changed(
        "jb/cases.json", c,
        "jb/cases.json case t2: field label: unknown field; label, reason and source live only",
    )
    e = copy.deepcopy(q.expectations)
    del e["t0"]
    q.write(q.files)
    q.write({"jb/cases.json": q.cases[1:], "jb/reference/expectations.json": e})
    q.check("jb/cases.json: 14 cases; a judgment set needs at least 15")
    q.changed("jb/cases.json", [dict(c, split="train") for c in q.cases],
              "jb/cases.json: no case in split held-out")


def calibration_shape(s: Scratch) -> None:
    """Evidence, nested model ban and every calibration field/type/range oracle."""
    q = JudgmentInputs(s)
    good: dict[str, object] = {
        "evidence": "evidence/jb.md", "held_out": {"accuracy": 1, "brier": 0},
        "threshold": {"accuracy_min": 0.699, "brier_max": 2.403, "accepted": False},
    }
    q.changed("jb/suite.json", {**q.suite, "calibration": {
        "evidence": "evidence/jb.md", "held_out": {"accuracy": 0.5, "brier": 0.6},
        "threshold": {"accuracy_min": 0.7, "brier_max": 0.39, "accepted": True},
    }}, None)
    variants: list[tuple[object, str]] = [
        ({**good, "why": "x"}, "calibration.why: unknown field"),
        ({k: v for k, v in good.items() if k != "evidence"}, "calibration.evidence: missing"),
        ("stub/p/q-1.2", "calibration: must be an object {evidence, held_out, threshold}"),
        ({**good, "evidence": "evidence/none.md"},
         "calibration.evidence: no file evidence/none.md beside evals/"),
        ({**good, "evidence": "../evidence/jb.md"},
         "calibration.evidence: must be a relative path inside the repo"),
    ]
    for value, expected in variants:
        q.changed(
            "jb/suite.json", {**q.suite, "calibration": value}, "jb/suite.json: field " + expected,
        )
    one = "a suite names no model; the kit's one judgment model is judgment-model.json"
    for extra, expected in (
        ({"calibration": {**good, "model": "stub/first"}}, "calibration.model"),
        ({"calibration": {**good, "held_out": {"accuracy": 1, "brier": 0, "model": "stub/first"}}},
         "calibration.held_out.model"),
        ({"chosen": {"model": "stub/p/q-1.2", "evidence": "evidence/jb.md"}}, "chosen"),
        ({"model": "stub/first"}, "model"),
    ):
        q.changed("jb/suite.json", {**q.suite, **extra}, f"jb/suite.json: field {expected}: {one}")
    calibration_fields(q, good)
    root = s.root / "trig"
    (root / "trig" / "reference").mkdir(parents=True)
    (root / "fixtures" / "fx").mkdir(parents=True)
    (root / "trig" / "suite.json").write_text(json.dumps({
        "suite": "trig", "kind": "skill-trigger", "description": "input",
        "calibration": {"evidence": "evidence/jb.md"},
    }))
    (root / "trig" / "cases.json").write_text(json.dumps([{
        "id": "reads", "role": "implementer", "fixture": "fx", "task": "Build it.",
        "should_trigger": True, "split": "train",
    }]))
    (root / "trig" / "reference" / "expectations.json").write_text(json.dumps({
        "reads": {"facts": [{"fact": "skill_read", "skill": "tdd"}]},
    }))
    got = s.run([kit("check-evals"), str(root)], want=1)
    assert "trig/suite.json: field calibration: only in a judgment suite" in got.out + got.err, got


def calibration_fields(q: JudgmentInputs, good: dict[str, object]) -> None:
    for key, fields in (
        ("held_out", {"accuracy": 1, "brier": 0}),
        ("threshold", {"accuracy_min": 0.699, "brier_max": 2.403, "accepted": False}),
    ):
        q.changed("jb/suite.json", {**q.suite, "calibration": {
            k: v for k, v in good.items() if k != key
        }}, f"jb/suite.json: field calibration.{key}: missing")
        q.changed("jb/suite.json", {**q.suite, "calibration": {**good, key: 0.7}},
                  f"jb/suite.json: field calibration.{key}: must be an object {{")
        q.changed("jb/suite.json", {**q.suite, "calibration": {**good, key: {**fields, "n": 7}}},
                  f"jb/suite.json: field calibration.{key}.n: unknown field")
        for field in fields:
            q.changed("jb/suite.json", {**q.suite, "calibration": {
                **good, key: {k: v for k, v in fields.items() if k != field}
            }}, f"jb/suite.json: field calibration.{key}.{field}: missing")
    for key, field, value, expected in (
        ("held_out", "accuracy", 1.2, "must be a number from 0 to 1, got 1.2"),
        ("held_out", "accuracy", "0.9", "must be a number from 0 to 1, got '0.9'"),
        ("held_out", "brier", 2.1, "must be a number from 0 to 2, got 2.1"),
        ("threshold", "accuracy_min", True, "must be a number from 0 to 1, got True"),
        ("threshold", "brier_max", -0.1, "must be a number from 0 up, got -0.1"),
        ("threshold", "accepted", "no", "must be true or false, got 'no'"),
    ):
        bounds: dict[str, object] = {"accuracy": 1, "brier": 0} if key == "held_out" else {
            "accuracy_min": 0.699, "brier_max": 2.403, "accepted": False,
        }
        bounds[field] = value
        q.changed("jb/suite.json", {**q.suite, "calibration": {**good, key: bounds}},
                  f"jb/suite.json: field calibration.{key}.{field}: {expected}")


def model_shape(s: Scratch) -> None:
    """The one model file, exact catalogue membership and evidence lookup."""
    q = JudgmentInputs(s)
    q.missing("judgment-model.json", f"{q.root}/judgment-model.json: missing; "
              "it holds the kit's one judgment model {model, evidence}")
    for field in ("model", "evidence"):
        q.changed("judgment-model.json", {k: v for k, v in q.model.items() if k != field},
                  f"judgment-model.json: field {field}: missing")
    q.changed("judgment-model.json", {**q.model, "why": "x"},
              "judgment-model.json: field why: unknown field")
    for model, expected in (
        ("stub/~x/y", "stub/~x/y is a moving alias in classifiers.json "
         "(owner: stub ruling, tests/qa.sh)"),
        ("stub/p/q-1.2:free", "stub/p/q-1.2:free is a moving alias in classifiers.json "
         "(owner: stub ruling, tests/qa.sh)"),
        ("stub/ynr", "stub/ynr is yes/no only in classifiers.json (ruling: stub yes/no ruling)"),
        ("stub/cheap-total", "stub/cheap-total is not in classifiers.json pinned"),
    ):
        q.changed("judgment-model.json", {**q.model, "model": model},
                  "judgment-model.json: field model: " + expected)
    for model in ("stub/p/q-latest", "stub/m-current"):
        q.changed("judgment-model.json", {**q.model, "model": model}, None)
    for model in ("stub", "stub/", "/x", "stub/a b", ""):
        q.changed(
            "judgment-model.json", {**q.model, "model": model},
            "judgment-model.json: field model: "
            f"must be a classifier <provider>/<id>, got '{model}'",
        )
    q.changed("judgment-model.json", {**q.model, "evidence": "evidence/none.md"},
              "judgment-model.json: field evidence: no file evidence/none.md beside evals/")


def catalogue_shape(s: Scratch) -> None:
    """Required catalogue keys, classifications, duplicates and rulings."""
    q = JudgmentInputs(s)
    q.missing("classifiers.json", f"{q.root}/classifiers.json: missing; "
              "it holds every catalogue classifier ruled")
    for field in ("owner", "moving_alias", "yes_no_only", "pinned"):
        q.changed("classifiers.json", {k: v for k, v in q.catalogue.items() if k != field},
                  f"classifiers.json: field {field}: missing")
    variants: list[tuple[dict[str, object], str]] = [
        ({"why": "x"}, "why: unknown field"),
        ({"owner": " "}, "owner: must be the ruling's source, one non-empty line"),
        ({"pinned": {**q.pinned, "stub": "r"}},
         "pinned.stub: must be a classifier <provider>/<id>, got 'stub'"),
        ({"pinned": {**q.pinned, "stub/first": " "}},
         "pinned.stub/first: must be its pinning ruling's source, one non-empty line"),
        ({"pinned": list(q.pinned)},
         "pinned: must be an object {<provider>/<id>: its ruling's source}"),
        ({"moving_alias": "stub/~x/y"}, "moving_alias: must be a list of classifier ids"),
        ({"pinned": {**q.pinned, "stub/~x/y": "r"}},
         "pinned.stub/~x/y: stub/~x/y already listed in moving_alias"),
        ({"moving_alias": ["stub/~x/y", "stub/x-latest:free", "stub/p/q-1.2:free", "stub/~x/y"]},
         "moving_alias[3]: stub/~x/y already listed in moving_alias"),
        ({"yes_no_only": ["stub/ynr"]},
         "yes_no_only: must be an object {<provider>/<id>: {ruling, error, evidence}}"),
        ({"yes_no_only": {"stub/ynr": q.yesno, "stub": q.yesno}},
         "yes_no_only.stub: must be a classifier <provider>/<id>, got 'stub'"),
        ({"yes_no_only": {"stub/ynr": q.yesno, "stub/~x/y": q.yesno}},
         "yes_no_only.stub/~x/y: stub/~x/y already listed in moving_alias"),
        ({"pinned": {**q.pinned, "stub/ynr": "r"}},
         "pinned.stub/ynr: stub/ynr already listed in yes_no_only"),
        ({"yes_no_only": {"stub/ynr": "r"}},
         "yes_no_only.stub/ynr: must be an object {ruling, error, evidence}, got 'r'"),
        ({"yes_no_only": {"stub/ynr": {**q.yesno, "why": "x"}}},
         "yes_no_only.stub/ynr.why: unknown field"),
    ]
    for changes, expected in variants:
        q.changed(
            "classifiers.json", {**q.catalogue, **changes}, "classifiers.json: field " + expected,
        )
    for key in ("ruling", "error", "evidence"):
        q.changed("classifiers.json", {**q.catalogue, "yes_no_only": {"stub/ynr": {
            k: v for k, v in q.yesno.items() if k != key
        }}}, f"classifiers.json: field yes_no_only.stub/ynr.{key}: missing")
        q.changed(
            "classifiers.json", {**q.catalogue, "yes_no_only": {"stub/ynr": {**q.yesno, key: " "}}},
            f"classifiers.json: field yes_no_only.stub/ynr.{key}: must be",
        )


if __name__ == "__main__":
    main(labels_shape, calibration_shape, model_shape, catalogue_shape)
