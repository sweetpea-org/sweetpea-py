import { BLOCK_LABELS, allBlocks, findFactor, updateBlock, type Block, type Constraint, type Model } from "../model";

type Props = { model: Model; onChange: (model: Model) => void };
type Field = "k" | "factor" | "level" | "anyLevel" | "index" | "trials" | "factors" | "optional";

const TYPES: Record<string, { label: string; help: string; fields: Field[] }> = {
  AtMostKInARow: { label: "At most K in a row", help: "A level (or any level of a factor) never repeats more than K trials in a row.", fields: ["k", "factor", "anyLevel"] },
  AtLeastKInARow: { label: "At least K in a row", help: "Whenever the level appears, it runs for at least K trials.", fields: ["k", "factor", "anyLevel"] },
  ExactlyKInARow: { label: "Exactly K in a row", help: "Whenever the level appears, it runs for exactly K trials.", fields: ["k", "factor", "anyLevel"] },
  ExactlyK: { label: "Exactly K times", help: "The level appears exactly K times in each sequence.", fields: ["k", "factor", "level"] },
  Exclude: { label: "Exclude a level", help: "The level never appears; trials that would produce it are left out.", fields: ["factor", "level"] },
  Pin: { label: "Pin a trial", help: "The trial at a position always has this level (0 is the first trial, -1 the last).", fields: ["index", "factor", "level"] },
  MinimumTrials: { label: "Minimum trials", help: "Each sequence has at least this many trials; the crossing repeats to fill them.", fields: ["trials"] },
  CoverAllCombinations: { label: "Cover all combinations", help: "Every combination of these factors' levels appears, sizing the sequence to fit. Optional factors are given up if needed.", fields: ["factors", "optional"] },
  LatinSquare: { label: "Latin square", help: "With N levels, every N trials include every level of each factor, and each run of N trials takes a different combination.", fields: ["factors"] },
  Sequential: { label: "Sequential", help: "The factor's levels appear in their listed order, starting over after the last.", fields: ["factor"] },
};

function blank(type: string, model: Model, crossed: string[]): Constraint {
  const factor = model.factors[0];
  const level = factor?.levels[0]?.name ?? null;
  const fields = TYPES[type].fields;
  return {
    type,
    ...(fields.includes("k") && { k: 2 }),
    ...(fields.includes("factor") && { factor: factor?.name }),
    ...(fields.includes("level") && { level }),
    ...(fields.includes("anyLevel") && { level: null }),
    ...(fields.includes("index") && { index: 0 }),
    ...(fields.includes("trials") && { trials: 24 }),
    ...(fields.includes("factors") && { factors: crossed.slice() }),
    ...(fields.includes("optional") && { optional: [] }),
  };
}

function FactorChecks({ model, chosen, onChange }: { model: Model; chosen: string[]; onChange: (names: string[]) => void }) {
  return (
    <span className="checks">
      {model.factors.map((f) => (
        <label key={f.name} className="check">
          <input type="checkbox" checked={chosen.includes(f.name)}
            onChange={() => onChange(model.factors.map((g) => g.name)
              .filter((n) => (n === f.name) !== chosen.includes(n)))} />
          {f.name}
        </label>
      ))}
    </span>
  );
}

function ConstraintCard({ model, constraint: c, onChange, onRemove }: {
  model: Model;
  constraint: Constraint;
  onChange: (c: Constraint) => void;
  onRemove: () => void;
}) {
  const { label, help, fields } = TYPES[c.type];
  const levels = findFactor(model, c.factor)?.levels ?? [];
  const number = (key: "k" | "index" | "trials") => (
    <input type="number" value={c[key]} onChange={(e) => onChange({ ...c, [key]: Math.round(Number(e.target.value)) })} />
  );

  return (
    <article className="card constraint">
      <header className="card-header">
        <h3>{label}</h3>
        <button className="small remove" onClick={onRemove}>Delete</button>
      </header>
      <p className="hint">{help}</p>
      <div className="fields">
        {fields.includes("k") && <label>K {number("k")}</label>}
        {fields.includes("index") && <label>Trial {number("index")}</label>}
        {fields.includes("trials") && <label>Trials {number("trials")}</label>}
        {fields.includes("factor") && (
          <label>
            Factor
            <select value={c.factor} onChange={(e) => onChange({ ...c, factor: e.target.value,
              level: c.level === null ? null : findFactor(model, e.target.value)?.levels[0]?.name ?? null })}>
              {model.factors.map((f) => <option key={f.name}>{f.name}</option>)}
            </select>
          </label>
        )}
        {(fields.includes("level") || fields.includes("anyLevel")) && (
          <label>
            Level
            <select value={JSON.stringify(c.level)} onChange={(e) => onChange({ ...c, level: JSON.parse(e.target.value) })}>
              {fields.includes("anyLevel") && <option value="null">any level</option>}
              {levels.map((l) => <option key={String(l.name)} value={JSON.stringify(l.name)}>{l.name}</option>)}
            </select>
          </label>
        )}
        {fields.includes("factors") && (
          <div>Factors <FactorChecks model={model} chosen={c.factors!} onChange={(factors) => onChange({ ...c, factors })} /></div>
        )}
        {fields.includes("optional") && (
          <div>Optional <FactorChecks model={model} chosen={c.optional!} onChange={(optional) => onChange({ ...c, optional })} /></div>
        )}
      </div>
    </article>
  );
}

export function scopeNote(block: Block): string {
  return block.type === "cross"
    ? "These apply within each run of this block."
    : "These apply across everything inside this block, including where its runs meet.";
}

/** The constraints of one block, edited in place. */
export function ConstraintList({ model, block, onChange }: Props & { block: Block }) {
  const set = (constraints: Constraint[]) =>
    onChange({ ...model, block: updateBlock(model.block, block.name, (b) => ({ ...b, constraints })) });
  const crossed = block.type === "cross" ? block.crossings[0] ?? [] : [];
  return (
    <div className="constraint-list">
      {block.constraints.map((c, i) => (
        <ConstraintCard key={i} model={model} constraint={c}
          onChange={(next) => set(block.constraints.map((d, j) => (j === i ? next : d)))}
          onRemove={() => set(block.constraints.filter((_, j) => j !== i))} />
      ))}
      <select value="" disabled={model.factors.length === 0}
        onChange={(e) => set([...block.constraints, blank(e.target.value, model, crossed)])}>
        <option value="">+ Constraint…</option>
        {Object.entries(TYPES).map(([type, t]) => <option key={type} value={type}>{t.label}</option>)}
      </select>
    </div>
  );
}

export default function ConstraintsPanel({ model, onChange }: Props) {
  return (
    <div className="constraints-panel">
      <p className="intro">
        Constraints shape the order of trials. Each belongs to a block, which sets where it applies. They can
        also be edited inside each block on the Blocks step.
      </p>
      {allBlocks(model.block).map((block) => (
        <section key={block.name} className="constraint-group">
          <h3>{block.name} <span className="badge">{BLOCK_LABELS[block.type]}</span></h3>
          <p className="hint">{scopeNote(block)}</p>
          <ConstraintList model={model} block={block} onChange={onChange} />
        </section>
      ))}
    </div>
  );
}
