"""Renders a GUI design (see ``gui/README.md`` for its JSON shape) as a
SweetPea program."""

import json
import keyword
import re
from typing import Dict, List

from sweetpea._internal.main import __all__ as SWEETPEA_NAMES

RESERVED = {"design", "crossing", "constraints", "block", "experiments", "sweetpea"} | set(SWEETPEA_NAMES)


def generate(model: dict) -> str:
    """The full program: definitions, then synthesis and printing."""
    run = ("experiments = synthesize_trials(block, {}, {})\n"
           "print_experiments(block, experiments)\n").format(model["samples"], model["sampler"])
    body = definitions(model) + run
    names = [n for n in SWEETPEA_NAMES if re.search(r"\b{}\b".format(n), body)]
    return _imports(names) + "\n" + body


def definitions(model: dict) -> str:
    """Factor, constraint, and block definitions, ending with ``block = ...``."""
    var = variable_names([f["name"] for f in model["factors"]])
    factors = "".join(_factor(f, var) + "\n" for f in model["factors"])
    constraints = "".join("    {},\n".format(_constraint(c, var)) for c in model["constraints"])
    complete = "" if model["requireCompleteCrossing"] else ", require_complete_crossing=False"
    return (factors + "\n"
            + "design = [{}]\n".format(", ".join(var[f["name"]] for f in model["factors"]))
            + "crossing = [{}]\n".format(", ".join(var[n] for n in model["crossing"]))
            + "constraints = [\n{}]\n".format(constraints)
            + "\nblock = CrossBlock(design, crossing, constraints{})\n".format(complete))


def variable_names(names: List[str]) -> Dict[str, str]:
    """A distinct Python identifier for each factor name."""
    var: Dict[str, str] = {}
    for name in names:
        base = re.sub(r"\W", "_", name) or "factor"
        if base[0].isdigit():
            base = "f_" + base
        candidate, n = base, 2
        while candidate in RESERVED or keyword.iskeyword(candidate) or candidate in var.values():
            candidate, n = "{}_{}".format(base, n), n + 1
        var[name] = candidate
    return var


def _imports(names: List[str]) -> str:
    rows = [", ".join(names[i:i + 4]) for i in range(0, len(names), 4)]
    return "from sweetpea import (\n" + "".join("    {},\n".format(r) for r in rows) + ")\n"


def _literal(value) -> str:
    """Strings in double quotes, as in SweetPea's documentation."""
    return json.dumps(value, ensure_ascii=False) if isinstance(value, str) else repr(value)


def _weighted(text: str, weight: int) -> str:
    return text if weight == 1 else "{}, {}".format(text, weight)


def _factor(factor: dict, var: Dict[str, str]) -> str:
    head = "{} = Factor({}, [".format(var[factor["name"]], _literal(factor["name"]))
    if factor["kind"] == "basic":
        return head + ", ".join(_basic_level(l) for l in factor["levels"]) + "])"
    levels = "".join("    {},\n".format(_derived_level(factor, l, var)) for l in factor["levels"])
    return head + "\n" + levels + "])"


def _basic_level(level: dict) -> str:
    if level["weight"] == 1:
        return _literal(level["name"])
    return "Level({}, {})".format(_literal(level["name"]), level["weight"])


def _derived_level(factor: dict, level: dict, var: Dict[str, str]) -> str:
    if level["rule"] is None:
        return "ElseLevel({})".format(_weighted(_literal(level["name"]), level["weight"]))
    params = ", ".join(var[n] for n in factor["inputs"])
    window = "{}(lambda {}: {}, [{}])".format(
        "WithinTrial" if factor["kind"] == "within" else "Transition",
        params, render_rule(level["rule"], factor["kind"], var), params)
    return "DerivedLevel({})".format(_weighted("{}, {}".format(_literal(level["name"]), window), level["weight"]))


def render_rule(rule: dict, kind: str, var: Dict[str, str]) -> str:
    """A rule as a Python boolean expression over the lambda's parameters."""
    if "cmp" in rule:
        return "{} {} {}".format(_term(rule["left"], kind, var), rule["cmp"], _term(rule["right"], kind, var))
    if "not" in rule:
        return "not " + _nested(rule["not"], kind, var)
    group = "all" if "all" in rule else "any"
    parts = [_nested(r, kind, var) for r in rule[group]]
    if not parts:
        return "True" if group == "all" else "False"
    return (" and " if group == "all" else " or ").join(parts)


def _nested(rule: dict, kind: str, var: Dict[str, str]) -> str:
    text = render_rule(rule, kind, var)
    # A one-member group renders as its member, which needs no parentheses.
    group = rule.get("all", rule.get("any"))
    return "({})".format(text) if group is not None and len(group) > 1 else text


def _term(term: dict, kind: str, var: Dict[str, str]) -> str:
    if "level" in term:
        return _literal(term["level"])
    if kind == "within":
        return var[term["factor"]]
    return "{}[{}]".format(var[term["factor"]], term["at"])


def _level_ref(ref: dict, var: Dict[str, str]) -> str:
    if ref["level"] is None:
        return var[ref["factor"]]
    return "({}, {})".format(var[ref["factor"]], _literal(ref["level"]))


def _constraint(c: dict, var: Dict[str, str]) -> str:
    kind = c["type"]
    if kind in ("AtMostKInARow", "AtLeastKInARow", "ExactlyKInARow", "ExactlyK"):
        return "{}({}, {})".format(kind, c["k"], _level_ref(c, var))
    if kind == "Exclude":
        return "Exclude({})".format(_level_ref(c, var))
    if kind == "Pin":
        return "Pin({}, {})".format(c["index"], _level_ref(c, var))
    if kind == "MinimumTrials":
        return "MinimumTrials({})".format(c["trials"])
    if kind == "Sequential":
        return "Sequential({})".format(var[c["factor"]])
    if kind == "LatinSquare":
        return "LatinSquare([{}])".format(", ".join(var[n] for n in c["factors"]))
    optional = ", optional=[{}]".format(", ".join(var[n] for n in c["optional"])) if c["optional"] else ""
    return "CoverAllCombinations({}{})".format(", ".join(var[n] for n in c["factors"]), optional)
