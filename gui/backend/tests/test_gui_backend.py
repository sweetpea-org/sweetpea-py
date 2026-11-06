from pathlib import Path

import pytest

import sweetpea
from sweetpea_gui.codegen import generate
from sweetpea_gui.examples import list_examples
from sweetpea_gui.parse import Unsupported, parse_program
from sweetpea_gui.run import DesignError, check, synthesize

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
    assert check(model)["trials"] == namespace["block"]._trials_per_sample()


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
    assert model["block"]["constraints"][0] == {"type": "AtMostKInARow", "k": 3, "factor": "color", "level": "red"}
    assert model["block"]["constraints"][1]["level"] is None
    assert (model["samples"], model["sampler"], model["block"]["requireCompleteCrossing"]) == (3, "RandomGen", False)
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
    ("x = Factor('x', ['a'])\nb = CrossBlock([x], [x], [])\nsynthesize_trials(b)\nsynthesize_trials(b)\n", 5),
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
    model["block"]["constraints"][0]["level"] = "missing"
    assert "error" in check(model)


def test_synthesize_returns_rows_per_trial():
    model = parse_program((EXAMPLES / "Simple.py").read_text())
    model["samples"] = 2
    result = synthesize(model)
    assert len(result["sequences"]) == 2
    assert all(len(rows) == check(model)["trials"] for rows in result["sequences"])


NESTED = '''
A = Factor("A", ["a1", "a2"])
B = Factor("B", ["b1", "b2"])
session = Factor("session", ["s1", "s2"])
day = Factor("day", ["d1", "d2"])
inner = CrossBlock([A, B], [A, B], [])
outer = CrossBlock([session], [session], [])
nb = Nest(outer_block=outer, inner_block=inner, constraints=[])
ordered = Merge([nb], constraints=[Sequential(session)])
nnb = Nest(CrossBlock([day], [day], []), ordered)
repeated = Repeat(inner, [MinimumTrials(8), AtMostKInARow(1, A)])
f3 = Factor("f3", ["x", "y", "z"])
multi = MultiCrossBlock([A, B, f3], [[A, B], [f3]], [], mode=RepeatMode.WEIGHT)
'''


@pytest.mark.parametrize("root, trials", [("nb", 8), ("ordered", 8), ("nnb", 16), ("repeated", 8), ("multi", 4)])
def test_block_structures_round_trip_with_sweetpea_trial_counts(root, trials):
    source = NESTED + "experiments = synthesize_trials({}, 1)\n".format(root)
    model = model_of(source)
    assert model["block"]["name"] == root
    assert parse_program(generate(model)) == model
    namespace: dict = {}
    exec("from sweetpea import *\n" + NESTED, namespace)
    nodes = check(model)["nodes"]
    assert nodes[root]["trials"] == namespace[root]._trials_per_sample() == trials
    assert all(nodes[n]["trials"] == namespace[n]._trials_per_sample() for n in nodes if n in namespace)


def test_nest_reads_outer_and_inner_blocks():
    block = model_of(NESTED + "synthesize_trials(nnb)\n")["block"]
    assert block["type"] == "nest" and block["outer"]["crossings"] == [["day"]]
    merge = block["inner"]
    assert merge["type"] == "merge" and merge["constraints"] == [{"type": "Sequential", "factor": "session"}]
    assert [merge["blocks"][0]["outer"]["name"], merge["blocks"][0]["inner"]["name"]] == ["outer", "inner"]


def test_inline_blocks_get_generated_names():
    block = model_of(NESTED + "synthesize_trials(nnb)\n")["block"]
    assert block["outer"]["name"] == "cross_block_1"


def test_modes_read_as_enum_or_string():
    as_enum = model_of(NESTED + "m = Merge([inner], mode=RepeatMode.WEIGHT, alignment=AlignmentMode.POST_PREAMBLE)\n")
    as_text = model_of(NESTED + "m = Merge([inner], mode='weight', alignment='post preamble')\n")
    assert as_enum == as_text
    assert (as_enum["block"]["mode"], as_enum["block"]["alignment"]) == ("weight", "post preamble")
    assert "mode=RepeatMode.WEIGHT" in generate(as_enum)


def test_root_defaults_to_last_block_created():
    assert model_of(NESTED)["block"]["name"] == "multi"


def test_single_crossing_with_mode_renders_as_multicrossblock():
    model = model_of(NESTED + "m = MultiCrossBlock([A], [[A]], [], mode=RepeatMode.REPEAT)\n")
    assert "m = MultiCrossBlock(" in generate(model)
    assert parse_program(generate(model)) == model


@pytest.mark.parametrize("example", list_examples(), ids=lambda e: e["title"])
def test_every_example_opens_in_the_gui(example):
    model = parse_program(example["code"])
    assert "trials" in check(model)


def _simple():
    return parse_program((EXAMPLES / "Simple.py").read_text())


def _factor(model, name):
    return next(f for f in model["factors"] if f["name"] == name)


def _only_otherwise(m):
    _factor(m, "volume")["levels"] = [l for l in _factor(m, "volume")["levels"] if l["rule"] is None]


def _overlap(m):
    _factor(m, "volume")["levels"][1]["rule"] = {
        "cmp": "==", "left": {"factor": "color", "at": 0}, "right": {"level": "red"}}


def _exclude_every_color(m):
    m["block"]["constraints"] += [{"type": "Exclude", "factor": "color", "level": l} for l in ("red", "blue")]


@pytest.mark.parametrize("mutate, expected", [
    (_only_otherwise, "“volume” needs at least one level with a condition"),
    (lambda m: _factor(m, "color").update(levels=[]), "“color” has no levels"),
    (lambda m: _factor(m, "volume")["levels"].append({"name": "quiet", "weight": 1, "rule": None}),
     "more than one “otherwise” level"),
    (_overlap, "Levels “yelling” and “normal” of “volume” both apply when color is red, size is large"),
    (lambda m: m["block"].update(design=["volume"], crossings=[["volume"]]), "which is computed from"),
    (lambda m: m["block"]["constraints"].append({"type": "Exclude", "factor": "color", "level": "purple"}),
     "“color” has no level “purple”"),
    (lambda m: m["block"]["constraints"].__setitem__(0, {"type": "AtMostKInARow", "k": 0, "factor": "color",
                                                          "level": None}), "K must be at least 1"),
    (lambda m: m["block"]["constraints"].append({"type": "MinimumTrials", "trials": 0}), "must be at least 1"),
    (lambda m: m["block"]["constraints"].append({"type": "Pin", "index": 50, "factor": "color", "level": "red"}),
     "the block has 4 trials, so use 0 to 3"),
    (_exclude_every_color, "Every level of “color” is excluded"),
    (lambda m: m["block"]["constraints"].append({"type": "LatinSquare", "factors": []}), "choose at least one factor"),
])
def test_design_mistakes_are_explained_in_gui_terms(mutate, expected):
    model = _simple()
    mutate(model)
    error = check(model)["error"]
    assert expected in error
    assert not any(code in error for code in ("Factor<", "arg is an empty sequence", "division", "('"))


def test_nest_crossing_a_factor_twice_is_explained():
    model = parse_program((EXAMPLES.parent / "gui" / "examples" / "nested_sessions.py").read_text())
    model["block"]["inner"]["inner"].update(design=["A", "B", "session"], crossings=[["A", "B", "session"]])
    assert "“session” is crossed in both the outer and the inner block" in check(model)["error"]


def test_synthesize_refuses_a_design_with_mistakes():
    model = _simple()
    _only_otherwise(model)
    with pytest.raises(DesignError, match="needs at least one level with a condition"):
        synthesize(model)
