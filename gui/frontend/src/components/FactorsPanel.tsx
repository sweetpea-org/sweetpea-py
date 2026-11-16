import { useState } from "react";
import {
  TEMPLATES, defaultRule, dropFactor, lagOf, leaves, renameFactor, renameLevel, ruleUses, uniqueName, updateBlock, usages,
  type Factor, type LeafBlock, type Level, type Model,
} from "../model";
import { MAX_ROWS, rowCount, toConditions, toEnumeration, withLag } from "../conditions";
import CommitInput from "./CommitInput";
import ConditionInput from "./ConditionInput";
import EnumerationTable from "./EnumerationTable";
// The click-to-build condition editor, kept for later; typed conditions replace it.
// import RuleEditor from "./RuleEditor";

type Props = { model: Model; onChange: (model: Model) => void };

// The type-a-name-then-Enter box for new levels, kept for later; "+ level" replaces it.
// function AddInput({ placeholder, onAdd }: { placeholder: string; onAdd: (text: string) => void }) {
//   const [text, setText] = useState("");
//   return (
//     <input
//       className="add-input"
//       title="Type a level name and press Enter to add it"
//       value={text}
//       placeholder={placeholder}
//       onChange={(e) => setText(e.target.value)}
//       onKeyDown={(e) => {
//         if (e.key === "Enter" && text.trim()) {
//           onAdd(text.trim());
//           setText("");
//         }
//       }}
//     />
//   );
// }

function Weight({ level, onChange }: { level: Level; onChange: (weight: number) => void }) {
  return (
    <label className="weight" title="How often this level appears relative to the others">
      <input type="number" min={1} value={level.weight}
        onChange={(e) => onChange(Math.max(1, Math.round(Number(e.target.value)) || 1))} />
    </label>
  );
}

function FactorCard({ model, index, onChange }: Props & { index: number }) {
  const [collapsed, setCollapsed] = useState(false);
  const factor = model.factors[index];
  const levelNames = factor.levels.map((l) => l.name);
  const earlier = model.factors.slice(0, index).map((f) => f.name);

  const update = (f: Factor) => onChange({ ...model, factors: model.factors.map((g, i) => (i === index ? f : g)) });
  const updateLevel = (i: number, l: Level) => update({ ...factor, levels: factor.levels.map((m, j) => (j === i ? l : m)) });
  const removeLevel = (i: number) => update({ ...factor, levels: factor.levels.filter((_, j) => j !== i) });

  function remove() {
    const used = usages(model, factor.name);
    if (used.length) {
      alert(`“${factor.name}” is used by ${used.join(", ")}. Remove those first.`);
      return;
    }
    onChange(dropFactor(model, factor.name));
  }

  const derived = factor.kind !== "basic";
  const enumerated = factor.define === "enumerate";
  const lag = lagOf(factor);

  // An enumerated factor's table has a column per input, and per trial compared, so new inputs
  // or a switch between "within" and "across" trials start the table over.
  const restarted = (f: Factor): Factor => ({ ...f, levels: f.levels.map((l) => ({ ...l, combos: [] })) });

  function setInputs(inputs: string[]) {
    if (enumerated) {
      update(restarted({ ...factor, inputs }));
      return;
    }
    // Conditions on a factor that is no longer an input start over.
    const levels = factor.levels.map((l) =>
      l.rule && factor.inputs!.some((n) => !inputs.includes(n) && ruleUses(l.rule!, n))
        ? { ...l, rule: defaultRule(model, inputs) } : l);
    update({ ...factor, inputs, levels });
  }

  function setLag(next: number) {
    const f = withLag(factor, next, defaultRule(model, factor.inputs!));
    update(enumerated && !next !== !lag ? restarted(f) : f);
  }

  function addLevel() {
    const name = uniqueName(levelNames, "level");
    const level: Level = !derived ? { name, weight: 1 }
      : enumerated ? { name, weight: 1, rule: null, combos: [] }
      : { name, weight: 1, rule: defaultRule(model, factor.inputs!) };
    update({ ...factor, levels: [...factor.levels, level] });
    setCollapsed(false);
  }

  const rows = derived ? rowCount(factor, model) : 0;

  const nameTaken = (others: string[]) => (text: string) => (others.includes(text) ? `“${text}” is already used` : null);
  const levelName = (level: Level) => (
    <CommitInput value={String(level.name)}
      validate={nameTaken(levelNames.filter((n) => n !== level.name).map(String))}
      onCommit={(name) => onChange(renameLevel(model, factor.name, level.name, name))} />
  );

  return (
    <article className={collapsed ? "card factor collapsed" : "card factor"}>
      <header className="card-header">
        <CommitInput className="factor-name" value={factor.name}
          validate={nameTaken(model.factors.map((f) => f.name).filter((n) => n !== factor.name))}
          onCommit={(name) => onChange(renameFactor(model, factor.name, name))} />
        <span className="badge">{derived ? "Derived factor" : "Factor"}</span>
        {collapsed && <span className="hint">{factor.levels.length} levels</span>}
        {!leaves(model.block).some((b) => b.design.includes(factor.name)) && (
          <span className="badge warning" title="Add it to a block's design on the Blocks step to include it in trials">
            Not in any block
          </span>
        )}
        <span className="card-actions">
          <button className="small add" title="Add a level to this factor" onClick={addLevel}>+ Level</button>
          <button className="small collapse" aria-expanded={!collapsed}
            title={collapsed ? "Show this factor's levels" : "Hide this factor's levels"}
            onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? "▸" : "▾"}
          </button>
          <button className="small remove" title="Delete factor" onClick={remove}>×</button>
        </span>
      </header>

      {collapsed ? null : !derived ? (
        factor.levels.length === 0 ? <p className="hint">No levels yet. Add one with + level.</p> : (
          <table className="level-table">
            <thead>
              <tr><th>Level</th><th>Weight</th><th aria-label="Remove" /></tr>
            </thead>
            <tbody>
              {factor.levels.map((level, i) => (
                <tr key={`${i}-${level.name}`}>
                  <td>{levelName(level)}</td>
                  <td><Weight level={level} onChange={(weight) => updateLevel(i, { ...level, weight })} /></td>
                  <td><button className="small remove" title="Remove level" onClick={() => removeLevel(i)}>×</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      ) : (
        <>
          <div className="derivation">
            <span>Based on</span>
            {factor.inputs!.map((name) => (
              <span className="chip" key={name}>
                {name}
                {factor.inputs!.length > 1 && (
                  <button className="small remove" title="Stop basing this factor on it"
                    onClick={() => setInputs(factor.inputs!.filter((n) => n !== name))}>×</button>
                )}
              </span>
            ))}
            {earlier.some((n) => !factor.inputs!.includes(n)) && (
              <select className="add" value="" title="Add a factor this one is computed from; only factors defined above it are listed"
                onChange={(e) => setInputs([...factor.inputs!, e.target.value])}>
                <option value="" hidden disabled>+ Factor</option>
                {earlier.filter((n) => !factor.inputs!.includes(n)).map((n) => <option key={n}>{n}</option>)}
              </select>
            )}
          </div>
          <div className="derivation">
            <span>Compare values</span>
            <select value={lag ? "across" : "within"} onChange={(e) => setLag(e.target.value === "across" ? 1 : 0)}
              title="Whether conditions look only at the current trial, or also at an earlier one">
              <option value="within">Within the same trial (lag = 0)</option>
              <option value="across">Across trials</option>
            </select>
            {lag > 0 && (
              <label className="lag" title="How many trials back to compare with: 1 is the previous trial">
                Lag =
                <input type="number" min={1} value={lag}
                  onChange={(e) => setLag(Math.max(1, Math.round(Number(e.target.value)) || 1))} />
              </label>
            )}
          </div>
          <div className="define-switch" role="group" aria-label="Define levels by">
            <span>Define levels by</span>
            <button className={enumerated ? "small" : "small on"} aria-pressed={!enumerated}
              title="Give each level a condition written in Python, such as color == word"
              onClick={() => enumerated && update(toConditions(factor))}>
              Function
            </button>
            <button className={enumerated ? "small on" : "small"} aria-pressed={enumerated}
              disabled={!enumerated && rows > MAX_ROWS}
              title={!enumerated && rows > MAX_ROWS
                ? `Too many combinations to list (${rows}; at most ${MAX_ROWS})`
                : "Choose the level for every combination of the inputs' levels"}
              onClick={() => !enumerated && update(toEnumeration(factor, model))}>
              Enumerate
            </button>
          </div>
          <div className="derived-levels">
            {factor.levels.map((level, i) => (
              <div className="derived-level" key={i}>
                <span className="badge">Level</span>
                {levelName(level)}
                <Weight level={level} onChange={(weight) => updateLevel(i, { ...level, weight })} />
                {enumerated ? (
                  <span className="hint combos">{(level.combos ?? []).length} of {rows} combinations</span>
                ) : (
                  <>
                    <select value={level.rule ? "when" : "otherwise"}
                      title="“when”: this level applies if its condition holds. “otherwise”: it applies when no other level does."
                      onChange={(e) =>
                      updateLevel(i, { ...level, rule: e.target.value === "when" ? defaultRule(model, factor.inputs!) : null })}>
                      <option value="when">When</option>
                      <option value="otherwise">Otherwise</option>
                    </select>
                    {level.rule ? (
                      <ConditionInput rule={level.rule} factor={factor} model={model}
                        onChange={(rule) => updateLevel(i, { ...level, rule })} />
                    ) : (
                      <span className="hint">No other level applies</span>
                    )}
                  </>
                )}
                <button className="small remove level-remove" title="Remove level" onClick={() => removeLevel(i)}>×</button>
              </div>
            ))}
          </div>
          {enumerated && <EnumerationTable factor={factor} model={model} onChange={update} />}
        </>
      )}
    </article>
  );
}

export default function FactorsPanel({ model, onChange }: Props) {
  const names = model.factors.map((f) => f.name);

  // A new factor joins the design of the first block, so that it shows up in trials.
  function add(factor: Factor) {
    const first = leaves(model.block)[0];
    onChange({
      ...model,
      factors: [...model.factors, factor],
      block: updateBlock(model.block, first.name, (b) => ({ ...b, design: [...(b as LeafBlock).design, factor.name] })),
    });
  }

  function addDerived(key: string) {
    const template = TEMPLATES[key];
    const factor = template.make(model, names.slice(0, template.inputs));
    add({ ...factor, name: uniqueName(names, factor.name) });
  }

  return (
    <div className="factors-panel">
      <p className="intro">
        Factors are the variables of an experiment; their levels vary from trial to trial. A{" "}
        <strong>derived factor</strong> is computed from other factors. The block structure decides how levels are
        combined and ordered across trials.
      </p>
      <div className="add-bar">
        <button className="add" title="A factor whose levels you list yourself"
          onClick={() => add({ name: uniqueName(names, "factor"), kind: "basic", levels: [] })}>
          + Factor
        </button>
        <button className="add" disabled={names.length === 0} title="A factor whose levels follow from other factors"
          onClick={() => addDerived("custom")}>
          + Derived factor
        </button>
        {/* Templates for common derived factors, kept for later:
        <select value="" onChange={(e) => addDerived(e.target.value)}>
          <option value="">+ Derived factor…</option>
          {Object.entries(TEMPLATES).map(([key, t]) => (
            <option key={key} value={key} disabled={names.length < t.inputs}>{t.label}</option>
          ))}
        </select> */}
      </div>
      {model.factors.map((_, i) => (
        <FactorCard key={i} model={model} index={i} onChange={onChange} />
      ))}
    </div>
  );
}
