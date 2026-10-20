"""Reads a SweetPea program back into a GUI design.

The program is interpreted, not executed: only the constructs that the GUI
can show are accepted, and anything else raises :class:`Unsupported` with the
line that caused it.
"""

import ast
from typing import Any, Dict, List, Optional

SAMPLERS = ["CMSGen", "IterateGen", "RandomGen"]
K_CONSTRAINTS = ["AtMostKInARow", "AtLeastKInARow", "ExactlyKInARow", "ExactlyK"]
# Calls whose only effect is output, which the GUI produces itself.
OUTPUT_CALLS = {"print_experiments", "tabulate_experiments", "save_experiments_csv", "print"}


class Unsupported(Exception):
    def __init__(self, node: Optional[ast.AST], message: str):
        super().__init__(message)
        self.line = getattr(node, "lineno", None)


class FactorRef:
    def __init__(self, name):
        self.name = name


class LevelSpec:
    """A ``Level``, ``DerivedLevel``, or ``ElseLevel`` before its factor exists."""
    def __init__(self, name, weight, window=None, is_else=False):
        self.name, self.weight, self.window, self.is_else = name, weight, window, is_else
        self.factor: Optional[str] = None


class Predicate:
    def __init__(self, params: List[str], body: ast.expr):
        self.params, self.body = params, body


class Sampler:
    def __init__(self, name):
        self.name = name


def parse_program(source: str) -> dict:
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise Unsupported(None, "Python syntax error: {}".format(e.msg)) from e
    program = _Program()
    for stmt in tree.body:
        program.statement(stmt)
    return program.model()


def _bind(node: ast.Call, params: List[str], defaults: Dict[str, Any]) -> Dict[str, ast.expr]:
    """Maps a call's positional and keyword arguments onto parameter names."""
    if len(node.args) > len(params) or any(isinstance(a, ast.Starred) for a in node.args):
        raise Unsupported(node, "too many arguments")
    args = dict(zip(params, node.args))
    for kw in node.keywords:
        if kw.arg not in params:
            raise Unsupported(node, "unexpected argument {}".format(kw.arg))
        args[kw.arg] = kw.value
    missing = [p for p in params if p not in args and p not in defaults]
    if missing:
        raise Unsupported(node, "missing argument {}".format(missing[0]))
    return args


def _function_body(node: ast.FunctionDef) -> ast.expr:
    """The boolean expression a predicate function returns."""
    stmts = [s for s in node.body
             if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    if len(stmts) == 1 and isinstance(stmts[0], ast.Return) and stmts[0].value is not None:
        return stmts[0].value
    if stmts and isinstance(stmts[0], ast.If) and len(stmts) <= 2:
        test = stmts[0]
        then, other = _returned_bool(test.body), _returned_bool(test.orelse or stmts[1:])
        if then is True and other is False:
            return test.test
        if then is False and other is True:
            return ast.UnaryOp(op=ast.Not(), operand=test.test)
    raise Unsupported(node, "the GUI reads predicate functions that only return a condition")


def _returned_bool(stmts: List[ast.stmt]) -> Optional[bool]:
    if len(stmts) == 1 and isinstance(stmts[0], ast.Return) and isinstance(stmts[0].value, ast.Constant):
        return stmts[0].value.value if isinstance(stmts[0].value.value, bool) else None
    return None


def _excerpt(node: ast.AST) -> str:
    text = ast.unparse(node)
    return text if len(text) <= 40 else text[:37] + "..."


def _negate(rule: dict) -> dict:
    if "cmp" in rule:
        return dict(rule, cmp="!=" if rule["cmp"] == "==" else "==")
    return {"not": rule}


class _Program:
    def __init__(self):
        self.env: Dict[str, Any] = {name: Sampler(name) for name in SAMPLERS}
        self.factors: Dict[str, dict] = {}
        self.block: Optional[dict] = None
        self.samples, self.sampler = 5, "CMSGen"

    def model(self) -> dict:
        if self.block is None:
            raise Unsupported(None, "the program must create a CrossBlock")
        return dict(factors=list(self.factors.values()), samples=self.samples, sampler=self.sampler,
                    **self.block)

    # Statements

    def statement(self, stmt: ast.stmt) -> None:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)) \
                or (isinstance(stmt, ast.Expr) and self.ignorable(stmt.value)):
            return
        if isinstance(stmt, ast.FunctionDef):
            self.env[stmt.name] = Predicate([a.arg for a in stmt.args.args], _function_body(stmt))
        elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            self.env[stmt.targets[0].id] = self.value(stmt.value)
        elif isinstance(stmt, ast.Expr):
            self.value(stmt.value)
        else:
            raise Unsupported(stmt, "the GUI can't show a {} statement".format(type(stmt).__name__))

    @staticmethod
    def ignorable(node: ast.expr) -> bool:
        """Docstrings, output calls, and ``sys.path`` setup."""
        if isinstance(node, ast.Constant):
            return True
        func = node.func if isinstance(node, ast.Call) else None
        if isinstance(func, ast.Name):
            return func.id in OUTPUT_CALLS
        return isinstance(func, ast.Attribute) and ast.unparse(func.value) == "sys.path"

    # Values

    def value(self, node: ast.expr) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
            return -node.operand.value
        if isinstance(node, ast.Name):
            if node.id not in self.env:
                raise Unsupported(node, "unknown name {}".format(node.id))
            return self.env[node.id]
        if isinstance(node, ast.List):
            return [self.value(e) for e in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self.value(e) for e in node.elts)
        if isinstance(node, ast.Lambda):
            return Predicate([a.arg for a in node.args.args], node.body)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            handler = getattr(self, "call_" + node.func.id, None)
            if handler is not None:
                return handler(node)
        raise Unsupported(node, "the GUI can't show {}".format(_excerpt(node)))

    def arguments(self, node: ast.Call, params: List[str], **defaults) -> Dict[str, Any]:
        args = _bind(node, params, defaults)
        return dict(defaults, **{p: self.value(v) for p, v in args.items()})

    def factor_name(self, node: ast.AST, value: Any) -> str:
        if not isinstance(value, FactorRef):
            raise Unsupported(node, "expected a factor")
        return value.name

    def factor_names(self, node: ast.AST, values: Any) -> List[str]:
        if not isinstance(values, list):
            raise Unsupported(node, "expected a list of factors")
        return [self.factor_name(node, v) for v in values]

    def level_ref(self, node: ast.AST, value: Any, factor_ok: bool) -> dict:
        if isinstance(value, FactorRef) and factor_ok:
            return {"factor": value.name, "level": None}
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], FactorRef):
            level = value[1].name if isinstance(value[1], LevelSpec) else value[1]
            return {"factor": value[0].name, "level": level}
        if isinstance(value, LevelSpec) and value.factor is not None:
            return {"factor": value.factor, "level": value.name}
        raise Unsupported(node, "expected a (factor, level) pair")

    # Factors and levels

    def call_Level(self, node):
        a = self.arguments(node, ["name", "weight"], weight=1)
        return LevelSpec(a["name"], a["weight"])

    def call_DerivedLevel(self, node):
        a = self.arguments(node, ["name", "window", "weight"], weight=1)
        return LevelSpec(a["name"], a["weight"], window=a["window"])

    def call_ElseLevel(self, node):
        a = self.arguments(node, ["name", "weight"], weight=1)
        return LevelSpec(a["name"], a["weight"], is_else=True)

    def window(self, node, kind):
        a = self.arguments(node, ["predicate", "factors"])
        if not isinstance(a["predicate"], Predicate):
            raise Unsupported(node, "expected a predicate function")
        return kind, a["predicate"], self.factor_names(node, a["factors"])

    def call_WithinTrial(self, node):
        return self.window(node, "within")

    def call_Transition(self, node):
        return self.window(node, "transition")

    def call_Factor(self, node):
        a = self.arguments(node, ["name", "initial_levels"])
        name, levels = a["name"], a["initial_levels"]
        if not isinstance(levels, list):
            raise Unsupported(node, "expected a list of levels")
        if name in self.factors:
            raise Unsupported(node, "factor {} is defined twice".format(name))
        derived = [l for l in levels if isinstance(l, LevelSpec) and (l.window or l.is_else)]
        if derived and len(derived) != len(levels):
            raise Unsupported(node, "factor {} mixes derived and plain levels".format(name))
        self.factors[name] = self.derived_factor(node, name, derived) if derived \
            else {"name": name, "kind": "basic", "levels": [self.basic_level(node, l) for l in levels]}
        return FactorRef(name)

    def basic_level(self, node, level):
        if isinstance(level, LevelSpec):
            return {"name": level.name, "weight": level.weight}
        if isinstance(level, tuple) and len(level) == 2:
            return {"name": level[0], "weight": level[1]}
        if isinstance(level, (str, int, float)):
            return {"name": level, "weight": 1}
        raise Unsupported(node, "the GUI can't show this level")

    def derived_factor(self, node, name, levels):
        windows = {(l.window[0], tuple(l.window[2])) for l in levels if l.window}
        if len(windows) != 1:
            raise Unsupported(node, "the levels of {} must share one derivation over the same factors".format(name))
        kind, inputs = windows.pop()
        result = []
        for level in levels:
            level.factor = name
            rule = None if level.is_else else self.rule(node, level.window[1], list(inputs), kind)
            result.append({"name": level.name, "weight": level.weight, "rule": rule})
        return {"name": name, "kind": kind, "inputs": list(inputs), "levels": result}

    # Predicates

    def rule(self, node, predicate: Predicate, inputs: List[str], kind: str) -> dict:
        if len(predicate.params) != len(inputs):
            raise Unsupported(node, "the predicate needs one parameter per factor")
        return self.condition(predicate.body, dict(zip(predicate.params, inputs)), kind)

    def condition(self, node: ast.expr, scope: Dict[str, str], kind: str) -> dict:
        if isinstance(node, ast.BoolOp):
            group = "all" if isinstance(node.op, ast.And) else "any"
            return {group: [self.condition(v, scope, kind) for v in node.values]}
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return _negate(self.condition(node.operand, scope, kind))
        if isinstance(node, ast.Constant) and isinstance(node.value, bool):
            return {"all": []} if node.value else {"any": []}
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            return self.comparison(node, scope, kind)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and isinstance(self.env.get(node.func.id), Predicate):
            return self.inline(node, scope, kind)
        raise Unsupported(node, "the GUI can't show the condition {}".format(_excerpt(node)))

    def comparison(self, node: ast.Compare, scope, kind) -> dict:
        op, right = node.ops[0], node.comparators[0]
        left = self.term(node.left, scope, kind)
        if isinstance(op, (ast.Eq, ast.NotEq)):
            return {"cmp": "==" if isinstance(op, ast.Eq) else "!=",
                    "left": left, "right": self.term(right, scope, kind)}
        if isinstance(op, (ast.In, ast.NotIn)) and isinstance(right, (ast.List, ast.Tuple, ast.Set)):
            rule = {"any": [{"cmp": "==", "left": left, "right": self.term(e, scope, kind)} for e in right.elts]}
            return rule if isinstance(op, ast.In) else _negate(rule)
        raise Unsupported(node, "the GUI reads ==, !=, and in comparisons")

    def term(self, node: ast.expr, scope, kind) -> dict:
        if isinstance(node, ast.Constant):
            return {"level": node.value}
        if kind == "within" and isinstance(node, ast.Name) and node.id in scope:
            return {"factor": scope[node.id], "at": 0}
        if kind == "transition" and isinstance(node, ast.Subscript) \
                and isinstance(node.value, ast.Name) and node.value.id in scope:
            at = self.value(node.slice)
            if at in (0, -1):
                return {"factor": scope[node.value.id], "at": at}
        raise Unsupported(node, "expected a factor or a level, not {}".format(_excerpt(node))
                          + ("; transitions use factor[0] (current) or factor[-1] (previous)"
                             if kind == "transition" else ""))

    def inline(self, node: ast.Call, scope, kind) -> dict:
        """Expands a call to another predicate function."""
        callee: Predicate = self.env[node.func.id]
        if len(node.args) != len(callee.params) or node.keywords \
                or not all(isinstance(a, ast.Name) and a.id in scope for a in node.args):
            raise Unsupported(node, "a predicate may call another only with its own parameters")
        inner = {p: scope[a.id] for p, a in zip(callee.params, node.args)}
        return self.condition(callee.body, inner, kind)

    # Constraints

    def k_constraint(self, node):
        a = self.arguments(node, ["k", "level"])
        return dict(type=node.func.id, k=a["k"], **self.level_ref(node, a["level"], True))

    call_AtMostKInARow = call_AtLeastKInARow = call_ExactlyKInARow = call_ExactlyK = k_constraint

    def call_Exclude(self, node):
        a = self.arguments(node, ["level"])
        return dict(type="Exclude", **self.level_ref(node, a["level"], False))

    def call_Pin(self, node):
        a = self.arguments(node, ["index", "level"])
        return dict(type="Pin", index=a["index"], **self.level_ref(node, a["level"], False))

    def call_MinimumTrials(self, node):
        return {"type": "MinimumTrials", "trials": self.arguments(node, ["trials"])["trials"]}

    def call_Sequential(self, node):
        a = self.arguments(node, ["factor"])
        return {"type": "Sequential", "factor": self.factor_name(node, a["factor"])}

    def call_LatinSquare(self, node):
        a = self.arguments(node, ["factors"])
        return {"type": "LatinSquare", "factors": self.factor_names(node, a["factors"])}

    def call_CoverAllCombinations(self, node):
        if node.keywords and [k.arg for k in node.keywords] != ["optional"]:
            raise Unsupported(node, "CoverAllCombinations takes factors and optional=[...]")
        optional = self.value(node.keywords[0].value) if node.keywords else []
        return {"type": "CoverAllCombinations",
                "factors": self.factor_names(node, [self.value(a) for a in node.args]),
                "optional": self.factor_names(node, optional)}

    # Block and synthesis

    def call_CrossBlock(self, node):
        if self.block is not None:
            raise Unsupported(node, "the GUI shows one block per program")
        a = self.arguments(node, ["design", "crossing", "constraints", "require_complete_crossing"],
                           require_complete_crossing=True)
        design = self.factor_names(node, a["design"])
        if sorted(design) != sorted(self.factors):
            raise Unsupported(node, "the design must list every factor exactly once")
        constraints = a["constraints"]
        if not isinstance(constraints, list) or not all(isinstance(c, dict) for c in constraints):
            raise Unsupported(node, "expected a list of constraints")
        self.block = {"crossing": self.factor_names(node, a["crossing"]), "constraints": constraints,
                      "requireCompleteCrossing": a["require_complete_crossing"]}
        return None

    def call_synthesize_trials(self, node):
        a = self.arguments(node, ["block", "samples", "sampling_strategy"],
                           samples=10, sampling_strategy=Sampler("IterateGen"))
        if not isinstance(a["sampling_strategy"], Sampler):
            raise Unsupported(node, "the GUI offers the samplers {}".format(", ".join(SAMPLERS)))
        self.samples, self.sampler = a["samples"], a["sampling_strategy"].name
        return None
