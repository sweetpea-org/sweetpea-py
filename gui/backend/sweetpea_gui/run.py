"""Builds and samples a GUI design by executing the code it generates, so the
GUI always runs exactly the program shown in its code pane."""

import contextlib
import io
from typing import Any, Dict

import sweetpea
from sweetpea._internal.main import __all__ as SWEETPEA_NAMES

from .codegen import definitions, post_order


def _blocks(model: dict) -> Dict[str, Any]:
    """Every block of the design by name, as SweetPea objects."""
    namespace: Dict[str, Any] = {n: getattr(sweetpea, n) for n in SWEETPEA_NAMES}
    exec(compile(definitions(model), "<design>", "exec"), namespace)
    return {b["name"]: namespace[b["name"]] for b in post_order(model["block"])}


def check(model: dict) -> dict:
    """Trials per sequence, with the trials and preamble of each block, or
    the error SweetPea reports for the design."""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            nodes = {name: {"trials": b._trials_per_sample(), "preamble": b.common_preamble_size()}
                     for name, b in _blocks(model).items()}
    except Exception as e:
        return {"error": str(e)}
    return {"trials": nodes[model["block"]["name"]]["trials"], "nodes": nodes}


def synthesize(model: dict) -> dict:
    """Sampled sequences as rows of {factor: level}, with SweetPea's printed log."""
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        block = _blocks(model)[model["block"]["name"]]
        experiments = sweetpea.synthesize_trials(block, model["samples"], getattr(sweetpea, model["sampler"]))
    return {"sequences": sweetpea.experiments_to_dicts(block, experiments), "log": log.getvalue()}
