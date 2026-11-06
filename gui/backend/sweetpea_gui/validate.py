"""Explains design mistakes in the GUI's terms.

``problems`` finds mistakes before SweetPea sees the design, where SweetPea
would otherwise fail with an internal error or report them in code terms.
``explain`` rewords whatever SweetPea still raises.
"""

import re
from typing import Dict, List, Set

from .codegen import post_order

K_TYPES = {"AtMostKInARow", "AtLeastKInARow", "ExactlyKInARow", "ExactlyK"}
# Exceptions that come from inside SweetPea rather than from its own checks.
INTERNAL = (ZeroDivisionError, TypeError, IndexError, KeyError, AttributeError, AssertionError)
INTERNAL_MESSAGES = re.compile(r"arg is an empty sequence|not enough values to unpack|index out of range")


def _q(name) -> str:
    return "“{}”".format(name)


def _leaves(block: dict) -> List[dict]:
    return [b for b in post_order(block) if b["type"] == "cross"]


def _design(block: dict) -> Set[str]:
    """Every factor a block's trials carry: the union of the designs inside it."""
    return {name for leaf in _leaves(block) for name in leaf["design"]}


# Constraint names as the Constraints step shows them.
LABELS = {
    "AtMostKInARow": "At most {k} in a row", "AtLeastKInARow": "At least {k} in a row",
    "ExactlyKInARow": "Exactly {k} in a row", "ExactlyK": "Exactly {k} times", "Exclude": "Exclude a level",
    "Pin": "Pin trial {index}", "MinimumTrials": "Minimum {trials} trials",
    "CoverAllCombinations": "Cover all combinations", "LatinSquare": "Latin square", "Sequential": "Sequential",
}


def _describe(c: dict) -> str:
    """A constraint as the GUI names it, such as “At most 2 in a row” on “color”."""
    subject = c.get("factor") or ", ".join(c.get("factors") or [])
    label = _q(LABELS.get(c["type"], c["type"]).format(**{k: c.get(k) for k in ("k", "index", "trials")}))
    return "{} on {}".format(label, _q(subject)) if subject else label


def problems(model: dict) -> List[str]:
    """Mistakes in the design, each as a sentence; empty when there are none."""
    factors: Dict[str, dict] = {f["name"]: f for f in model["factors"]}
    found: List[str] = []

    for f in model["factors"]:
        if not f["levels"]:
            found.append("{} has no levels. Add at least one level.".format(_q(f["name"])))
        elif f["kind"] != "basic":
            otherwise = [l["name"] for l in f["levels"] if l["rule"] is None]
            if len(otherwise) == len(f["levels"]):
                found.append("{} needs at least one level with a condition. An “otherwise” level only "
                             "covers what the other levels don't.".format(_q(f["name"])))
            if len(otherwise) > 1:
                found.append("{} has more than one “otherwise” level ({}). Keep one.".format(
                    _q(f["name"]), ", ".join(map(_q, otherwise))))

    for block in post_order(model["block"]):
        name = _q(block["name"])
        if block["type"] == "cross":
            design = set(block["design"])
            for crossing in block["crossings"]:
                for missing in [n for n in crossing if n not in design]:
                    found.append("Block {} crosses {} but doesn't include it in its design.".format(name, _q(missing)))
            for derived in [factors[n] for n in block["design"] if n in factors and factors[n]["kind"] != "basic"]:
                missing = [n for n in derived["inputs"] if n not in design]
                if missing:
                    found.append("Block {} includes {}, which is computed from {}. Add {} to the block's design too."
                                 .format(name, _q(derived["name"]), ", ".join(map(_q, derived["inputs"])),
                                         ", ".join(map(_q, missing))))
        if block["type"] == "nest":
            outer = {n for leaf in _leaves(block["outer"]) for c in leaf["crossings"] for n in c}
            inner = {n for leaf in _leaves(block["inner"]) for c in leaf["crossings"] for n in c}
            for both in sorted(outer & inner):
                found.append("{} is crossed in both the outer and the inner block of nest {}. Cross it in only one of them."
                             .format(_q(both), name))
        found.extend(_constraint_problems(block, factors))
    return found


def _constraint_problems(block: dict, factors: Dict[str, dict]) -> List[str]:
    found: List[str] = []
    design = _design(block)
    excluded: Dict[str, Set[str]] = {}
    for c in block["constraints"]:
        where = "The constraint {} in block {}".format(_describe(c), _q(block["name"]))
        named = [c["factor"]] if c.get("factor") else list(c.get("factors") or []) + list(c.get("optional") or [])
        for n in [n for n in named if n not in design]:
            found.append("{}: {} isn't in this block's design. Add it to the block, or move the constraint "
                         "to a block that has it.".format(where, _q(n)))
        level = c.get("level")
        if c.get("factor") in factors and level is not None \
                and level not in [l["name"] for l in factors[c["factor"]]["levels"]]:
            found.append("{}: {} has no level {}. Choose one of its levels.".format(where, _q(c["factor"]), _q(level)))
        if c["type"] in K_TYPES and c.get("k", 1) < 1:
            found.append("{}: K must be at least 1. To rule a level out entirely, use “Exclude a level”.".format(where))
        if c["type"] == "MinimumTrials" and c.get("trials", 1) < 1:
            found.append("{}: the number of trials must be at least 1.".format(where))
        if c["type"] in ("CoverAllCombinations", "LatinSquare") and not c.get("factors"):
            found.append("{}: choose at least one factor.".format(where))
        if c["type"] == "Exclude" and c.get("factor"):
            excluded.setdefault(c["factor"], set()).add(level)
    for name, levels in excluded.items():
        if name in factors and {l["name"] for l in factors[name]["levels"]} <= levels:
            found.append("Every level of {} is excluded in block {}, so no trial is possible.".format(
                _q(name), _q(block["name"])))
    return found


def pin_problems(model: dict, nodes: Dict[str, dict]) -> List[str]:
    """Pins outside their block's trials, which SweetPea would only report as finding no sequences."""
    found: List[str] = []
    for block in post_order(model["block"]):
        trials = nodes[block["name"]]["trials"]
        for c in block["constraints"]:
            if c["type"] == "Pin" and not -trials <= c["index"] < trials:
                found.append("The constraint “Pin trial {}” in block {}: the block has {} trials, so use 0 to {}, "
                             "or -1 for the last.".format(c["index"], _q(block["name"]), trials, trials - 1))
    return found


def explain(error: Exception, model: dict) -> str:
    """SweetPea's message for a design error, reworded for the GUI."""
    if isinstance(error, INTERNAL) or INTERNAL_MESSAGES.search(str(error)):
        return ("SweetPea couldn't build this design ({}). Look for a factor without levels, a derived factor "
                "with no conditions, or constraints that rule out every trial.".format(error))
    args = error.args
    # SweetPea raises some errors as ("Who", "what went wrong").
    text = "{}: {}".format(*args) if len(args) == 2 and all(isinstance(a, str) for a in args) else str(error)
    text = re.sub(r"Factor<([^>]*)>", lambda m: _q(m.group(1)), text)
    overlap = re.match(r"Factor (.+) matches (.+) and (.+) with assignment \[(.*)\]\.?$", text)
    if overlap:
        factor, first, second, values = overlap.groups()
        derived = next((f for f in model["factors"] if f["name"] == factor), None)
        values = [v.strip(" '\"") for v in values.split(",")]
        when = ", ".join("{} is {}".format(n, v) for n, v in zip(derived["inputs"], values)) if derived else ", ".join(values)
        return ("Levels {} and {} of {} both apply when {}. Each combination must fit exactly one level."
                .format(_q(first), _q(second), _q(factor), when))
    return text
