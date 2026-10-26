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

export type Mode = "weight" | "repeat" | "equal";
export type Alignment = "post preamble" | "parallel start" | "equal preamble";

type BlockBase = { name: string; constraints: Constraint[] };
export type LeafBlock = BlockBase & {
  type: "cross";
  design: string[];
  crossings: string[][];
  requireCompleteCrossing: boolean;
  mode: Mode | null;
  alignment: Alignment | null;
};
export type NestBlock = BlockBase & { type: "nest"; outer: Block; inner: Block; alignment: Alignment | null };
export type MergeBlock = BlockBase & { type: "merge"; blocks: Block[]; mode: Mode | null; alignment: Alignment | null };
export type RepeatBlock = BlockBase & { type: "repeat"; block: Block };
export type Block = LeafBlock | NestBlock | MergeBlock | RepeatBlock;

export type Model = {
  factors: Factor[];
  block: Block;
  samples: number;
  sampler: string;
};

export type BlockSize = { trials: number; preamble: number };
export type Check = { trials?: number; error?: string; nodes?: Record<string, BlockSize> };

export const SAMPLERS = ["CMSGen", "IterateGen", "RandomGen"];

export const BLOCK_LABELS: Record<Block["type"], string> = {
  cross: "Block", nest: "Nest", merge: "Merge", repeat: "Repeat",
};

export const newLeaf = (name: string, design: string[] = []): LeafBlock => ({
  type: "cross", name, design, crossings: [design], constraints: [],
  requireCompleteCrossing: true, mode: null, alignment: null,
});

export const STARTER: Model = {
  factors: [
    { name: "color", kind: "basic", levels: ["red", "blue", "green"].map((name) => ({ name, weight: 1 })) },
    { name: "word", kind: "basic", levels: ["red", "blue", "green"].map((name) => ({ name, weight: 1 })) },
  ],
  block: newLeaf("block", ["color", "word"]),
  samples: 3,
  sampler: "CMSGen",
};

// Blocks

export function children(block: Block): Block[] {
  if (block.type === "nest") return [block.outer, block.inner];
  if (block.type === "merge") return block.blocks;
  if (block.type === "repeat") return [block.block];
  return [];
}

/** Every block, each before the blocks it contains. */
export function allBlocks(block: Block): Block[] {
  return [block, ...children(block).flatMap(allBlocks)];
}

function withChildren(block: Block, f: (child: Block) => Block): Block {
  if (block.type === "nest") return { ...block, outer: f(block.outer), inner: f(block.inner) };
  if (block.type === "merge") return { ...block, blocks: block.blocks.map(f) };
  if (block.type === "repeat") return { ...block, block: f(block.block) };
  return block;
}

/** Replaces the named block with ``f`` of it. */
export function updateBlock(root: Block, name: string, f: (block: Block) => Block): Block {
  return root.name === name ? f(root) : withChildren(root, (c) => updateBlock(c, name, f));
}

/** Applies ``f`` to every block, innermost first. */
export function mapBlocks(root: Block, f: (block: Block) => Block): Block {
  return f(withChildren(root, (c) => mapBlocks(c, f)));
}

export const leaves = (block: Block) => allBlocks(block).filter((b): b is LeafBlock => b.type === "cross");

/** A block's crossings as read aloud, such as "color × word". */
export const crossingTitle = (block: LeafBlock) =>
  block.crossings.map((c) => c.join(" × ")).join(" + ") || "nothing crossed";

/** How many times a Repeat runs its block, or undefined before the sizes are known. */
export function runs(block: RepeatBlock, nodes: Record<string, BlockSize> | undefined): number | undefined {
  const total = nodes?.[block.name];
  const child = nodes?.[block.block.name];
  if (!total || !child || child.trials <= child.preamble) return undefined;
  // The preamble trials come once, before the first run.
  return Math.ceil((total.trials - child.preamble) / (child.trials - child.preamble));
}

// Names a block may not take: Python keywords and the names generated code uses.
const RESERVED = new Set([
  "and", "as", "assert", "break", "class", "continue", "def", "del", "elif", "else", "except", "False",
  "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "None", "nonlocal", "not",
  "or", "pass", "raise", "return", "True", "try", "while", "with", "yield", "experiments", "sweetpea",
  "Factor", "Level", "DerivedLevel", "ElseLevel", "WithinTrial", "Transition", "CrossBlock",
  "MultiCrossBlock", "Nest", "Merge", "Repeat", "RepeatMode", "AlignmentMode", "synthesize_trials",
  "print_experiments", "AtMostKInARow", "AtLeastKInARow", "ExactlyKInARow", "ExactlyK", "Exclude", "Pin",
  "MinimumTrials", "CoverAllCombinations", "LatinSquare", "Sequential", ...SAMPLERS,
]);

/** Why a block name is not allowed, or null. */
export function blockNameProblem(model: Model, name: string, current: string): string | null {
  if (!/^[A-Za-z_]\w*$/.test(name)) return "Use letters, digits and _, not starting with a digit";
  if (RESERVED.has(name)) return `“${name}” is reserved`;
  const taken = [...allBlocks(model.block).map((b) => b.name), ...model.factors.map((f) => f.name)];
  return name !== current && taken.includes(name) ? `“${name}” is already used` : null;
}

export const uniqueBlockName = (model: Model, base: string) =>
  uniqueName([...allBlocks(model.block).map((b) => b.name), ...model.factors.map((f) => f.name)], base);

export type Wrapper = "nest" | "merge" | "repeat";

/** Puts a container around the named block. A new Nest holds the block as
 * its inner block, under a new empty outer block. */
export function wrapBlock(model: Model, name: string, kind: Wrapper, trials: number): Block {
  const wrapperName = uniqueBlockName(model, kind);
  return updateBlock(model.block, name, (block): Block => {
    if (kind === "nest") {
      const outer = newLeaf(uniqueName([wrapperName, ...allBlocks(model.block).map((b) => b.name)], "outer"));
      return { type: "nest", name: wrapperName, outer, inner: block, constraints: [], alignment: null };
    }
    if (kind === "merge") return { type: "merge", name: wrapperName, blocks: [block], constraints: [], mode: null, alignment: null };
    // A Repeat runs its block again until MinimumTrials is met; start with two runs.
    return { type: "repeat", name: wrapperName, block, constraints: [{ type: "MinimumTrials", trials: trials * 2 }] };
  });
}

/** Replaces a container with the block it was wrapped around. */
export function unwrapBlock(root: Block, name: string): Block {
  return updateBlock(root, name, (b) => (b.type === "nest" ? b.inner : children(b)[0] ?? b));
}

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
const FACTOR_KEYS = new Set(["factor", "inputs", "design", "crossings", "factors", "optional"]);

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
    block: mapBlocks(model.block, (b) => ({
      ...b,
      constraints: b.constraints.map((c) => (c.factor === factor && c.level === from ? { ...c, level: to } : c)),
    })),
  };
}

/** Removes a factor, along with its place in every block's design and crossings. */
export function dropFactor(model: Model, name: string): Model {
  const drop = (names: string[]) => names.filter((n) => n !== name);
  return {
    ...model,
    factors: model.factors.filter((f) => f.name !== name),
    block: mapBlocks(model.block, (b) =>
      b.type === "cross" ? { ...b, design: drop(b.design), crossings: b.crossings.map(drop) } : b),
  };
}

/** Names of the factors and constraints that refer to a factor. */
export function usages(model: Model, name: string): string[] {
  const factors = model.factors.filter((f) => f.inputs?.includes(name)).map((f) => `factor “${f.name}”`);
  const constraints = allBlocks(model.block).flatMap((b) => b.constraints
    .filter((c) => c.factor === name || c.factors?.includes(name) || c.optional?.includes(name))
    .map((c) => `constraint ${c.type} in ${b.name}`));
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
