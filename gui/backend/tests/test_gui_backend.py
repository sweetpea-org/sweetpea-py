from pathlib import Path

import pytest

import sweetpea
from sweetpea_gui.codegen import generate
from sweetpea_gui.parse import Unsupported, parse_program
from sweetpea_gui.run import check, synthesize

EXAMPLES = Path(__file__).resolve().parents[3] / "example_programs"
READABLE_EXAMPLES = ["Simple.py", "Stroop_simple.py", "Stroop_congruency_balanced.py",
                     "TaskSwitching_simple.py", "TaskSwitching_challenging.py",
                     "PadmalaPessoa2011.py", "Manuscript_Example1_Stroop.py"]


def model_of(source: str) -> dict:
    return parse_program("from sweetpea import *\n" + source)


@pytest.mark.parametrize("name", READABLE_EXAMPLES)
def test_generated_code_reads_back_as_the_same_design(name):
    model = parse_program((EXAMPLES / name).read_text())
    assert parse_program(generate(model)) == model


@pytest.mark.parametrize("name", READABLE_EXAMPLES)
def test_generated_code_builds_the_example_block(name, monkeypatch):
    monkeypatch.setattr(sweetpea, "synthesize_trials", lambda *_, **__: [])
    monkeypatch.setattr(sweetpea, "print_experiments", lambda *_: None)
    namespace: dict = {}
    exec((EXAMPLES / name).read_text(), namespace)
    model = parse_program((EXAMPLES / name).read_text())
    assert check(model) == {"trials": namespace["block"]._trials_per_sample()}


def test_rule_forms_read_as_conditions():
    model = model_of('''
color = Factor("color", ["red", "blue", "green"])
word = Factor("word", ["red", "blue", "green"])
def warm(c):
    if c in ("red", "green"):
        return True
    else:
        return False
def same(c, w):
    """Congruent."""
    return c == w
kind = Factor("kind", [
    DerivedLevel("warm_same", WithinTrial(lambda c, w: warm(c) and same(c, w), [color, word])),
    DerivedLevel("cold_diff", WithinTrial(lambda c, w: not (c == "red" or same(c, w)), [color, word]), 2),
    ElseLevel("other"),
])
block = CrossBlock([color, word, kind], [color, word], [])
''')
    levels = model["factors"][2]["levels"]
    red, green = ({"cmp": "==", "left": {"factor": "color", "at": 0}, "right": {"level": l}}
                  for l in ("red", "green"))
    same = {"cmp": "==", "left": {"factor": "color", "at": 0}, "right": {"factor": "word", "at": 0}}
    assert levels[0]["rule"] == {"all": [{"any": [red, green]}, same]}
    assert levels[1] == {"name": "cold_diff", "weight": 2, "rule": {"not": {"any": [red, same]}}}
    assert levels[2] == {"name": "other", "weight": 1, "rule": None}


def test_transition_rule_reads_trial_positions():
    model = model_of('''
task = Factor("task", ["a", "b"])
shift = Factor("shift", [
    DerivedLevel("switch", Transition(lambda t: t[0] != t[-1], [task])),
    DerivedLevel("stay", Transition(lambda t: t[0] == t[-1], [task])),
])
block = CrossBlock([task, shift], [task, shift], [])
''')
    assert model["factors"][1]["kind"] == "transition"
    assert model["factors"][1]["levels"][0]["rule"] == {
        "cmp": "!=", "left": {"factor": "task", "at": 0}, "right": {"factor": "task", "at": -1}}
    assert "lambda task: task[0] != task[-1]" in generate(model)


def test_constraints_and_weights_round_trip():
    model = model_of('''
color = Factor("color", [Level("red", 2), "blue"])
size = Factor("size", ["big", "small"])
k = 3
constraints = [AtMostKInARow(k, (color, "red")), ExactlyK(2, size), Exclude((size, "big")),
               Pin(0, (color, "blue")), MinimumTrials(12), CoverAllCombinations(color, optional=[size])]
block = CrossBlock([color, size], [color], constraints, require_complete_crossing=False)
experiments = synthesize_trials(block, 3, RandomGen)
''')
    assert model["factors"][0]["levels"] == [{"name": "red", "weight": 2}, {"name": "blue", "weight": 1}]
    assert model["constraints"][0] == {"type": "AtMostKInARow", "k": 3, "factor": "color", "level": "red"}
    assert model["constraints"][1]["level"] is None
    assert (model["samples"], model["sampler"], model["requireCompleteCrossing"]) == (3, "RandomGen", False)
    assert parse_program(generate(model)) == model


def test_factor_names_become_distinct_identifiers():
    model = model_of('''
a = Factor("block", ["x"])
b = Factor("2 back", ["x"])
c = Factor("2_back", ["x"])
block = CrossBlock([a, b, c], [a], [])
''')
    code = generate(model)
    assert 'block_2 = Factor("block"' in code
    assert "f_2_back = " in code and "f_2_back_2 = " in code
    assert parse_program(code) == model


@pytest.mark.parametrize("source, line", [
    ("x = Factor('x', ['a'])\nfor i in []:\n    pass\n", 3),
    ("x = Factor('x', ['a'])\ny = Factor('y', [DerivedLevel('d', WithinTrial(lambda v: len(v) > 1, [x]))])\n", 3),
    ("x = Factor('x', ['a'])\nblock = CrossBlock([], [x], [])\n", 3),
])
def test_unsupported_code_reports_its_line(source, line):
    with pytest.raises(Unsupported) as e:
        model_of(source)
    assert e.value.line == line


def test_check_reports_sweetpea_errors():
    model = model_of('''
x = Factor("x", ["a", "b"])
block = CrossBlock([x], [x], [AtMostKInARow(1, (x, "a"))])
''')
    model["constraints"][0]["level"] = "missing"
    assert "error" in check(model)


def test_synthesize_returns_rows_per_trial():
    model = parse_program((EXAMPLES / "Simple.py").read_text())
    model["samples"] = 2
    result = synthesize(model)
    assert len(result["sequences"]) == 2
    assert all(len(rows) == check(model)["trials"] for rows in result["sequences"])
