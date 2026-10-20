// The design model shared with the Python server; see gui/README.md.

export type Value = string | number;
export type Term = { factor: string; at: number } | { level: Value };
export type Rule =
  | { cmp: "==" | "!="; left: Term; right: Term }
  | { all: Rule[] }
  | { any: Rule[] }
  | { not: Rule };

export type Kind = "basic" | "within" | "transition";
export type Level = { name: Value; weight: number; rule?: Rule | null };
export type Factor = { name: string; kind: Kind; inputs?: string[]; levels: Level[] };

export type Constraint = {
  type: string;
  k?: number;
  factor?: string;
  level?: Value | null;
  index?: number;
  trials?: number;
  factors?: string[];
  optional?: string[];
};

export type Model = {
  factors: Factor[];
  crossing: string[];
  constraints: Constraint[];
  requireCompleteCrossing: boolean;
  samples: number;
  sampler: string;
};

export type Check = { trials?: number; error?: string };

export const SAMPLERS = ["CMSGen", "IterateGen", "RandomGen"];

export const STARTER: Model = {
  factors: [
    { name: "color", kind: "basic", levels: ["red", "blue", "green"].map((name) => ({ name, weight: 1 })) },
    { name: "word", kind: "basic", levels: ["red", "blue", "green"].map((name) => ({ name, weight: 1 })) },
  ],
  crossing: ["color", "word"],
  constraints: [],
  requireCompleteCrossing: true,
  samples: 3,
  sampler: "CMSGen",
};

export const factorTerm = (factor: string, at = 0): Term => ({ factor, at });

export const isRef = (t: Term): t is { factor: string; at: number } => "factor" in t;

export function findFactor(model: Model, name: string | undefined): Factor | undefined {
  return model.factors.find((f) => f.name === name);
}

export function uniqueName(taken: Value[], base: string): string {
  let name = base;
  for (let n = 2; taken.includes(name); n++) name = `${base}${n}`;
  return name;
}

/** A rule that holds for the first level of the first input. */
export function defaultRule(model: Model, inputs: string[]): Rule {
  const first = findFactor(model, inputs[0]);
  return { cmp: "==", left: factorTerm(inputs[0]), right: { level: first?.levels[0]?.name ?? "" } };
}

/** Whether a rule mentions a factor. */
export function ruleUses(rule: Rule, factor: string): boolean {
  if ("cmp" in rule) return [rule.left, rule.right].some((t) => isRef(t) && t.factor === factor);
  if ("not" in rule) return ruleUses(rule.not, factor);
  return ("all" in rule ? rule.all : rule.any).some((r) => ruleUses(r, factor));
}

// Keys whose string values name factors, at any depth of the model.
const FACTOR_KEYS = new Set(["factor", "inputs", "crossing", "factors", "optional"]);

function mapFactorRefs(value: unknown, key: string, rename: (name: string) => string): unknown {
  if (typeof value === "string") return FACTOR_KEYS.has(key) ? rename(value) : value;
  if (Array.isArray(value)) return value.map((v) => mapFactorRefs(v, key, rename));
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, mapFactorRefs(v, k, rename)]));
  }
  return value;
}

export function renameFactor(model: Model, from: string, to: string): Model {
  const next = mapFactorRefs(model, "", (n) => (n === from ? to : n)) as Model;
  return { ...next, factors: next.factors.map((f) => (f.name === from ? { ...f, name: to } : f)) };
}

function renameLevelInRule(rule: Rule, factor: string, from: Value, to: Value): Rule {
  if ("cmp" in rule) {
    const fix = (term: Term, other: Term): Term =>
      !isRef(term) && term.level === from && isRef(other) && other.factor === factor ? { level: to } : term;
    return { ...rule, left: fix(rule.left, rule.right), right: fix(rule.right, rule.left) };
  }
  if ("not" in rule) return { not: renameLevelInRule(rule.not, factor, from, to) };
  return "all" in rule
    ? { all: rule.all.map((r) => renameLevelInRule(r, factor, from, to)) }
    : { any: rule.any.map((r) => renameLevelInRule(r, factor, from, to)) };
}

export function renameLevel(model: Model, factor: string, from: Value, to: Value): Model {
  return {
    ...model,
    factors: model.factors.map((f) => ({
      ...f,
      levels: f.levels.map((l) => ({
        ...l,
        name: f.name === factor && l.name === from ? to : l.name,
        rule: l.rule && renameLevelInRule(l.rule, factor, from, to),
      })),
    })),
    constraints: model.constraints.map((c) =>
      c.factor === factor && c.level === from ? { ...c, level: to } : c,
    ),
  };
}

/** Names of the factors and constraints that refer to a factor. */
export function usages(model: Model, name: string): string[] {
  const factors = model.factors.filter((f) => f.inputs?.includes(name)).map((f) => `factor “${f.name}”`);
  const constraints = model.constraints
    .filter((c) => c.factor === name || c.factors?.includes(name) || c.optional?.includes(name))
    .map((c) => `constraint ${c.type}`);
  return [...factors, ...constraints];
}

// Templates for derived factors that experiments commonly need.

export type Template = { label: string; inputs: number; make: (model: Model, inputs: string[]) => Factor };

export const TEMPLATES: Record<string, Template> = {
  congruency: {
    label: "Congruency — two factors match or not",
    inputs: 2,
    make: (_, [a, b]) => ({
      name: "congruency",
      kind: "within",
      inputs: [a, b],
      levels: [
        { name: "congruent", weight: 1, rule: { cmp: "==", left: factorTerm(a), right: factorTerm(b) } },
        { name: "incongruent", weight: 1, rule: { cmp: "!=", left: factorTerm(a), right: factorTerm(b) } },
      ],
    }),
  },
  transition: {
    label: "Repeat / switch — compared with the previous trial",
    inputs: 1,
    make: (_, [a]) => ({
      name: `${a}_transition`,
      kind: "transition",
      inputs: [a],
      levels: [
        { name: "repeat", weight: 1, rule: { cmp: "==", left: factorTerm(a, 0), right: factorTerm(a, -1) } },
        { name: "switch", weight: 1, rule: { cmp: "!=", left: factorTerm(a, 0), right: factorTerm(a, -1) } },
      ],
    }),
  },
  mapping: {
    label: "Mapping — one level for each level of another factor",
    inputs: 1,
    make: (model, [a]) => ({
      name: "response",
      kind: "within",
      inputs: [a],
      levels: (findFactor(model, a)?.levels ?? []).map((l, i) => ({
        name: `response_${i + 1}`,
        weight: 1,
        rule: { cmp: "==", left: factorTerm(a), right: { level: l.name } },
      })),
    }),
  },
  custom: {
    label: "Custom — write your own conditions",
    inputs: 1,
    make: (model, inputs) => ({
      name: "derived",
      kind: "within",
      inputs,
      levels: [
        { name: "yes", weight: 1, rule: defaultRule(model, inputs) },
        { name: "otherwise", weight: 1, rule: null },
      ],
    }),
  },
};
