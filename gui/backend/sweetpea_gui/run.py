"""Builds and samples a GUI design by executing the code it generates, so the
GUI always runs exactly the program shown in its code pane."""

import contextlib
import io
from typing import Any, Dict

import sweetpea
from sweetpea._internal.main import __all__ as SWEETPEA_NAMES

from .codegen import definitions, post_order
from .validate import explain, pin_problems, problems


def _blocks(model: dict) -> Dict[str, Any]:
    """Every block of the design by name, as SweetPea objects."""
    namespace: Dict[str, Any] = {n: getattr(sweetpea, n) for n in SWEETPEA_NAMES}
    exec(compile(definitions(model), "<design>", "exec"), namespace)
    return {b["name"]: namespace[b["name"]] for b in post_order(model["block"])}


class DesignError(Exception):
    """A design mistake, already worded for the GUI."""


def _build(model: dict) -> Dict[str, Any]:
    """The design's blocks with their sizes, or ``DesignError`` explaining why they can't be built."""
    found = problems(model)
    if found:
        raise DesignError("\n".join(found))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            blocks = _blocks(model)
            nodes = {name: {"trials": b._trials_per_sample(), "preamble": b.common_preamble_size()}
                     for name, b in blocks.items()}
    except Exception as e:
        raise DesignError(explain(e, model)) from e
    found = pin_problems(model, nodes)
    if found:
        raise DesignError("\n".join(found))
    return {"blocks": blocks, "nodes": nodes}


def check(model: dict) -> dict:
    """Trials per sequence, with the trials and preamble of each block, or
    what is wrong with the design."""
    try:
        nodes = _build(model)["nodes"]
    except DesignError as e:
        return {"error": str(e)}
    return {"trials": nodes[model["block"]["name"]]["trials"], "nodes": nodes}


def synthesize(model: dict) -> dict:
    """Sampled sequences as rows of {factor: level}, with SweetPea's printed log."""
    block = _build(model)["blocks"][model["block"]["name"]]
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):
            experiments = sweetpea.synthesize_trials(block, model["samples"], getattr(sweetpea, model["sampler"]))
    except Exception as e:
        raise DesignError(explain(e, model)) from e
    return {"sequences": sweetpea.experiments_to_dicts(block, experiments), "log": log.getvalue()}
