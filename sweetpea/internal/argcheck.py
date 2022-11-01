
from typing import Iterable

def argcheck(who, val, pred_or_type, what):
    pred = (lambda v: isinstance(v, pred_or_type)) if isinstance(pred_or_type, type) else pred_or_type
    if not pred(val):
        raise ValueError(f"{who}: expected {what}, given {val}")

def make_islistof(pred_or_type):
    pred = (lambda v: isinstance(v, pred_or_type)) if isinstance(pred_or_type, type) else pred_or_type
    return (lambda l: isinstance(l, Iterable) and all([pred(v) for v in l]))

def make_istuple(preds_or_types):
    def make_pred(pred_or_type):
        return (lambda v: isinstance(v, pred_or_type)) if isinstance(pred_or_type, type) else pred_or_type
    preds = [make_pred(pred_or_type) for pred_or_type in preds_or_types]
    return (lambda l: isinstance(l, tuple) and len(l) == len(preds_or_types) and all([pred(v) for pred, v in zip(preds, l)]))
