"""Builds and samples a GUI design by executing the code it generates, so the
GUI always runs exactly the program shown in its code pane."""

import contextlib
import io
from typing import Any, Dict

import sweetpea
from sweetpea._internal.main import __all__ as SWEETPEA_NAMES

from .codegen import definitions


def _block(model: dict):
    namespace: Dict[str, Any] = {n: getattr(sweetpea, n) for n in SWEETPEA_NAMES}
    exec(compile(definitions(model), "<design>", "exec"), namespace)
    return namespace["block"]


def check(model: dict) -> dict:
    """The trials per sequence, or the error SweetPea reports for the design."""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return {"trials": _block(model)._trials_per_sample()}
    except Exception as e:
        return {"error": str(e)}


def synthesize(model: dict) -> dict:
    """Sampled sequences as rows of {factor: level}, with SweetPea's printed log."""
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        block = _block(model)
        experiments = sweetpea.synthesize_trials(block, model["samples"], getattr(sweetpea, model["sampler"]))
    return {"sequences": sweetpea.experiments_to_dicts(block, experiments), "log": log.getvalue()}
