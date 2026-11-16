// Derived-level conditions written as Python expressions, and the combination tables of
// enumerated factors. Text is only read into the rule structure in model.ts, never run.

import { findFactor, isRef, lagOf, type Factor, type Model, type Rule, type Term, type Value } from "./model";

// Names

const KEYWORDS = new Set(["False", "None", "True", "and", "as", "assert", "async", "await", "break", "class",
  "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "in",
  "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"]);

/** The Python name a condition uses for a factor, as in the generated code. */
export function paramName(name: string): string {
  const base = name.replace(/\W/g, "_") || "factor";
  const safe = /^\d/.test(base) ? `f_${base}` : base;
  return KEYWORDS.has(safe) ? `${safe}_2` : safe;
}

/** How a condition refers to a factor in a given trial: `color`, or `color[0]` / `color[-1]`. */
export const refText = (factor: Factor, name: string, at: number) =>
  lagOf(factor) ? `${paramName(name)}[${at}]` : paramName(name);

const back = (lag: number) => (lag === 1 ? "the previous trial" : `${lag} trials back`);

// Reading text

type Token = { type: "punct" | "op" | "str" | "num" | "name"; text: string; value?: Value };

type Node =
  | { t: "name"; id: string }
  | { t: "sub"; id: string; index: number }
  | { t: "const"; value: Value | boolean }
  | { t: "seq"; open: string; elts: Node[] }
  | { t: "bool"; op: "and" | "or"; values: Node[] }
  | { t: "not"; operand: Node }
  | { t: "cmp"; op: "==" | "!=" | "in" | "not in"; left: Node; right: Node };

class ConditionError extends Error {}

function tokenize(text: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;
  while (i < text.length) {
    const rest = text.slice(i);
    const space = rest.match(/^\s+/);
    const quoted = rest.match(/^"([^"]*)"|^'([^']*)'/);
    const number = rest.match(/^\d+(\.\d+)?/);
    const name = rest.match(/^[A-Za-z_]\w*/);
    const op = rest.match(/^(==|!=)/);
    let token: Token;
    if (space) { i += space[0].length; continue; }
    if (op) token = { type: "op", text: op[0] };
    else if ("()[]{},-".includes(rest[0])) token = { type: "punct", text: rest[0] };
    else if (quoted) token = { type: "str", text: quoted[0], value: quoted[1] ?? quoted[2] };
    else if (number) token = { type: "num", text: number[0], value: Number(number[0]) };
    else if (name) token = { type: "name", text: name[0] };
    else if (rest[0] === "=") throw new ConditionError("Use == to compare (a single = assigns)");
    else if (/^["']/.test(rest)) throw new ConditionError("A quote isn't closed");
    else throw new ConditionError(`Python doesn't allow “${rest[0]}” here`);
    tokens.push(token);
    i += token.text.length;
  }
  return tokens;
}

function parseExpression(tokens: Token[]): Node {
  let at = 0;
  const peek = () => tokens[at];
  const is = (text: string, offset = 0) => tokens[at + offset]?.text === text && tokens[at + offset]?.type !== "str";
  const where = () => (peek() ? ` before “${peek().text}”` : " at the end");
  const expect = (text: string) => {
    if (!is(text)) throw new ConditionError(`Expected “${text}”${where()}`);
    at++;
  };

  function sequence(open: string, close: string): Node {
    const elts: Node[] = [];
    let comma = false;
    while (!is(close)) {
      elts.push(or());
      if (!is(",")) break;
      at++;
      comma = true;
    }
    expect(close);
    // (x) is x in brackets; (x,) and (x, y) are tuples.
    return open === "(" && elts.length === 1 && !comma ? elts[0] : { t: "seq", open, elts };
  }

  function atom(): Node {
    const token = peek();
    if (!token) throw new ConditionError("Expected a value at the end");
    at++;
    if (token.type === "str" || token.type === "num") return { t: "const", value: token.value! };
    if (token.text === "-" && peek()?.type === "num") return { t: "const", value: -tokens[at++].value! };
    if (token.text === "(") return sequence("(", ")");
    if (token.text === "[") return sequence("[", "]");
    if (token.text === "{") return sequence("{", "}");
    if (token.text === "True" || token.text === "False") return { t: "const", value: token.text === "True" };
    if (token.type !== "name" || KEYWORDS.has(token.text)) throw new ConditionError(`Expected a value before “${token.text}”`);
    if (is("(")) throw new ConditionError(`“${token.text}(…)” calls a function; use ==, !=, in, and, or, not instead`);
    if (!is("[")) return { t: "name", id: token.text };
    at++;
    const negative = is("-") ? (at++, -1) : 1;
    const index = peek()?.type === "num" && Number.isInteger(peek().value) ? (tokens[at++].value as number) * negative : null;
    if (index === null) throw new ConditionError(`Expected a trial number inside ${token.text}[ ]`);
    expect("]");
    return { t: "sub", id: token.text, index };
  }

  function comparison(): Node {
    const left = atom();
    const op = is("==") || is("!=") || is("in") ? peek().text : is("not") && is("in", 1) ? "not in" : null;
    if (!op) return left;
    at += op === "not in" ? 2 : 1;
    const node: Node = { t: "cmp", op: op as "==" | "!=" | "in" | "not in", left, right: atom() };
    if (is("==") || is("!=") || is("in")) throw new ConditionError("Compare two things at a time; join comparisons with and / or");
    return node;
  }

  function not(): Node {
    if (is("not")) { at++; return { t: "not", operand: not() }; }
    return comparison();
  }

  const joined = (op: "and" | "or", part: () => Node) => (): Node => {
    const values = [part()];
    while (is(op)) { at++; values.push(part()); }
    return values.length === 1 ? values[0] : { t: "bool", op, values };
  };
  const and = joined("and", not);
  const or = joined("or", and);

  const node = or();
  if (at < tokens.length) throw new ConditionError(`Unexpected “${peek().text}”; join conditions with and / or`);
  return node;
}

const show = (n: Node): string =>
  n.t === "name" ? n.id : n.t === "sub" ? `${n.id}[${n.index}]` : n.t === "const" ? JSON.stringify(n.value) : "this";

/** Reads a condition, checking it against the factor's inputs and their levels. */
export function parseCondition(text: string, factor: Factor, model: Model): { rule: Rule } | { error: string } {
  const inputs = factor.inputs ?? [];
  const lag = lagOf(factor);
  const byParam = new Map(inputs.map((n) => [paramName(n), n]));
  const levelOfInput = (id: string) => inputs.find((n) => findFactor(model, n)?.levels.some((l) => l.name === id));
  const trials = (p: string) => `${p}[0] for this trial and ${p}[-${lag}] for ${back(lag)}`;

  function input(id: string): string {
    const name = byParam.get(id);
    if (name) return name;
    const owner = levelOfInput(id);
    throw new ConditionError(owner ? `Put levels in quotes: "${id}"`
      : `“${id}” isn't a factor this one is based on (${[...byParam.keys()].join(", ")})`);
  }

  function term(n: Node): Term {
    if (n.t === "const" && typeof n.value !== "boolean") return { level: n.value };
    if (n.t === "name") {
      const name = input(n.id);
      if (lag) throw new ConditionError(`Across trials, write ${trials(n.id)}`);
      return { factor: name, at: 0 };
    }
    if (n.t === "sub") {
      const name = input(n.id);
      if (!lag) throw new ConditionError(`Within the same trial, write ${n.id} without [${n.index}]`);
      if (n.index !== 0 && n.index !== -lag) throw new ConditionError(`Write ${trials(n.id)}`);
      return { factor: name, at: n.index };
    }
    throw new ConditionError(`Expected a factor or a level, not ${show(n)}`);
  }

  const items = (n: Node, what: string) => {
    if (n.t !== "seq") throw new ConditionError(`After in, list ${what} in brackets, such as ("red", "blue")`);
    return n.elts;
  };

  function condition(n: Node): Rule {
    if (n.t === "bool") return { [n.op === "and" ? "all" : "any"]: n.values.map(condition) } as Rule;
    if (n.t === "not") return negate(condition(n.operand));
    if (n.t === "const" && typeof n.value === "boolean") return n.value ? { all: [] } : { any: [] };
    if (n.t !== "cmp") throw new ConditionError(`${show(n)} on its own isn't a condition; compare it, such as ${show(n)} == "…"`);
    let rule: Rule;
    if (n.op === "==" || n.op === "!=") {
      rule = { cmp: n.op, left: term(n.left), right: term(n.right) };
    } else if (n.left.t === "seq") {
      // (a, b) in {("x", "y"), …}: one of the listed combinations.
      const keys = n.left.elts.map(term);
      rule = {
        any: items(n.right, "the combinations").map((row) => {
          if (row.t !== "seq" || row.elts.length !== keys.length) {
            throw new ConditionError(`Each combination needs ${keys.length} levels, one per factor`);
          }
          return { all: keys.map((k, i): Rule => ({ cmp: "==", left: k, right: term(row.elts[i]) })) };
        }),
      };
    } else {
      const left = term(n.left);
      rule = { any: items(n.right, "the levels").map((e): Rule => ({ cmp: "==", left, right: term(e) })) };
    }
    return n.op === "not in" ? negate(rule) : rule;
  }

  // As the server reads code: `not a == b` is `a != b`.
  const negate = (r: Rule): Rule => ("cmp" in r ? { ...r, cmp: r.cmp === "==" ? "!=" : "==" } : { not: r });

  try {
    const tokens = tokenize(text);
    if (tokens.length === 0) return { error: "Type a condition, such as color == word" };
    const rule = condition(parseExpression(tokens));
    const problem = levelProblem(rule, model);
    return problem ? { error: problem } : { rule };
  } catch (e) {
    return { error: (e as Error).message };
  }
}

/** A level compared with a factor that doesn't have it. */
function levelProblem(rule: Rule, model: Model): string | null {
  if ("cmp" in rule) {
    const [ref, value] = isRef(rule.left) && !isRef(rule.right) ? [rule.left, rule.right]
      : isRef(rule.right) && !isRef(rule.left) ? [rule.right, rule.left] : [null, null];
    if (ref && value && !(findFactor(model, ref.factor)?.levels ?? []).some((l) => l.name === value.level)) {
      return `“${value.level}” isn't a level of ${ref.factor}`;
    }
    return null;
  }
  if ("not" in rule) return levelProblem(rule.not, model);
  return ("all" in rule ? rule.all : rule.any).map((r) => levelProblem(r, model)).find((p) => p) ?? null;
}

// Writing text: the same expression as the generated code's lambda.

const literal = (v: Value) => (typeof v === "number" ? String(v) : JSON.stringify(v));

/** A condition as Python. */
export function ruleText(rule: Rule, factor: Factor): string {
  const term = (t: Term) => (isRef(t) ? refText(factor, t.factor, t.at) : literal(t.level));
  // `color in ("red", "blue")`: one factor having one of two or more levels.
  const membership = (r: Rule): string | null => {
    const members = "any" in r ? r.any : [];
    const first = members[0];
    const same = (m: Rule) => "cmp" in m && m.cmp === "==" && isRef(m.left) && !isRef(m.right)
      && "cmp" in first && JSON.stringify(m.left) === JSON.stringify(first.left);
    if (members.length < 2 || !members.every(same) || !("cmp" in first)) return null;
    return `${term(first.left)} in (${members.map((m) => "cmp" in m ? term(m.right) : "").join(", ")})`;
  };
  const text = (r: Rule): string => {
    if ("cmp" in r) return `${term(r.left)} ${r.cmp} ${term(r.right)}`;
    if ("not" in r) return membership(r.not)?.replace(" in (", " not in (") ?? `not ${nested(r.not)}`;
    const listed = membership(r);
    if (listed) return listed;
    const parts = ("all" in r ? r.all : r.any).map(nested);
    if (parts.length === 0) return "all" in r ? "True" : "False";
    return parts.join("all" in r ? " and " : " or ");
  };
  // A one-member group prints as its member, which needs no brackets.
  const nested = (r: Rule) => {
    const group = "all" in r ? r.all : "any" in r ? r.any : null;
    return group && group.length > 1 && !membership(r) ? `(${text(r)})` : text(r);
  };
  return text(rule);
}

/** The factor looking `lag` trials back (0: within a trial); comparisons with the earlier trial
 * follow it, and conditions that can no longer be written start over. */
export function withLag(factor: Factor, lag: number, fallback: Rule): Factor {
  const relag = (r: Rule): Rule => {
    if ("cmp" in r) {
      const move = (t: Term): Term => (isRef(t) && t.at < 0 ? { ...t, at: -lag } : t);
      return { ...r, left: move(r.left), right: move(r.right) };
    }
    if ("not" in r) return { not: relag(r.not) };
    return "all" in r ? { all: r.all.map(relag) } : { any: r.any.map(relag) };
  };
  const looksBack = (r: Rule): boolean => ("cmp" in r ? [r.left, r.right].some((t) => isRef(t) && t.at < 0)
    : "not" in r ? looksBack(r.not) : ("all" in r ? r.all : r.any).some(looksBack));
  const { lag: _, ...rest } = factor;
  return {
    ...rest,
    kind: lag ? "transition" : "within",
    ...(lag > 1 ? { lag } : {}),
    levels: factor.levels.map((l) => ({
      ...l,
      rule: l.rule && (lag ? relag(l.rule) : looksBack(l.rule) ? fallback : l.rule),
    })),
  };
}

// Enumerated factors

export type Key = { factor: string; at: number };

// Past this many rows, a table is too long to fill in by hand.
export const MAX_ROWS = 64;

/** The table's columns: each input, and across trials its earlier and current trial. */
export function enumerationKeys(factor: Factor): Key[] {
  const inputs = factor.inputs ?? [];
  const lag = lagOf(factor);
  return lag
    ? inputs.flatMap((n) => [{ factor: n, at: -lag }, { factor: n, at: 0 }])
    : inputs.map((n) => ({ factor: n, at: 0 }));
}

export const keyLabel = (key: Key, factor: Factor) =>
  lagOf(factor) ? `${key.factor} (${key.at === 0 ? "this trial" : back(-key.at)})` : key.factor;

/** Every combination of the keys' levels, one per table row. */
export function enumerationRows(factor: Factor, model: Model): Value[][] {
  return enumerationKeys(factor).reduce<Value[][]>(
    (rows, key) => rows.flatMap((row) => (findFactor(model, key.factor)?.levels ?? []).map((l) => [...row, l.name])),
    [[]]);
}

export const rowCount = (factor: Factor, model: Model) =>
  enumerationKeys(factor).reduce((n, key) => n * (findFactor(model, key.factor)?.levels.length ?? 0), 1);

export const sameRow = (a: Value[], b: Value[]) => a.length === b.length && a.every((v, i) => v === b[i]);

function holds(rule: Rule, value: (t: Term) => Value): boolean {
  if ("cmp" in rule) return (value(rule.left) === value(rule.right)) === (rule.cmp === "==");
  if ("not" in rule) return !holds(rule.not, value);
  return "all" in rule ? rule.all.every((r) => holds(r, value)) : rule.any.some((r) => holds(r, value));
}

/** The factor as a table: each row goes to the first level whose condition holds, or to the
 * "otherwise" level when none does. */
export function toEnumeration(factor: Factor, model: Model): Factor {
  const keys = enumerationKeys(factor);
  const owner = (row: Value[]) => {
    const value = (t: Term) => (isRef(t) ? row[keys.findIndex((k) => k.factor === t.factor && k.at === t.at)] : t.level);
    const match = factor.levels.findIndex((l) => l.rule && holds(l.rule, value));
    return match >= 0 ? match : factor.levels.findIndex((l) => !l.rule);
  };
  const rows = enumerationRows(factor, model);
  return {
    ...factor,
    define: "enumerate",
    levels: factor.levels.map((l, i) => ({ ...l, rule: null, combos: rows.filter((row) => owner(row) === i) })),
  };
}

/** The factor with conditions again: each level holds for exactly the rows it had. */
export function toConditions(factor: Factor): Factor {
  const keys = enumerationKeys(factor);
  const rowRule = (row: Value[]): Rule => {
    const parts = keys.map((k, i): Rule => ({ cmp: "==", left: { factor: k.factor, at: k.at }, right: { level: row[i] } }));
    return parts.length === 1 ? parts[0] : { all: parts };
  };
  const { define: _, ...rest } = factor;
  return {
    ...rest,
    levels: factor.levels.map(({ combos, ...l }) => {
      const rows = (combos ?? []).map(rowRule);
      return { ...l, rule: rows.length === 1 ? rows[0] : { any: rows } };
    }),
  };
}
