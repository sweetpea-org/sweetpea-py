import { useState } from "react";
import {
  TEMPLATES, defaultRule, dropFactor, leaves, renameFactor, renameLevel, ruleUses, uniqueName, updateBlock, usages,
  type Factor, type Kind, type LeafBlock, type Level, type Model,
} from "../model";
import CommitInput from "./CommitInput";
import RuleEditor from "./RuleEditor";

type Props = { model: Model; onChange: (model: Model) => void };

function AddInput({ placeholder, onAdd }: { placeholder: string; onAdd: (text: string) => void }) {
  const [text, setText] = useState("");
  return (
    <input
      className="add-input"
      value={text}
      placeholder={placeholder}
      onChange={(e) => setText(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter" && text.trim()) {
          onAdd(text.trim());
          setText("");
        }
      }}
    />
  );
}

function Weight({ level, onChange }: { level: Level; onChange: (weight: number) => void }) {
  return (
    <label className="weight" title="How often this level appears relative to the others">
      <input type="number" min={1} value={level.weight}
        onChange={(e) => onChange(Math.max(1, Math.round(Number(e.target.value)) || 1))} />
    </label>
  );
}

function FactorCard({ model, index, onChange }: Props & { index: number }) {
  const factor = model.factors[index];
  const levelNames = factor.levels.map((l) => l.name);
  const earlier = model.factors.slice(0, index).map((f) => f.name);

  const update = (f: Factor) => onChange({ ...model, factors: model.factors.map((g, i) => (i === index ? f : g)) });
  const updateLevel = (i: number, l: Level) => update({ ...factor, levels: factor.levels.map((m, j) => (j === i ? l : m)) });

  function remove() {
    const used = usages(model, factor.name);
    if (used.length) {
      alert(`“${factor.name}” is used by ${used.join(", ")}. Remove those first.`);
      return;
    }
    onChange(dropFactor(model, factor.name));
  }

  function setInputs(inputs: string[]) {
    // Conditions on a factor that is no longer an input start over.
    const levels = factor.levels.map((l) =>
      l.rule && factor.inputs!.some((n) => !inputs.includes(n) && ruleUses(l.rule!, n))
        ? { ...l, rule: defaultRule(model, inputs) } : l);
    update({ ...factor, inputs, levels });
  }

  const nameTaken = (others: string[]) => (text: string) => (others.includes(text) ? `“${text}” is already used` : null);

  return (
    <article className="card factor">
      <header className="card-header">
        <CommitInput className="factor-name" value={factor.name}
          validate={nameTaken(model.factors.map((f) => f.name).filter((n) => n !== factor.name))}
          onCommit={(name) => onChange(renameFactor(model, factor.name, name))} />
        <span className="badge">{factor.kind === "basic" ? "factor" : "derived factor"}</span>
        {!leaves(model.block).some((b) => b.design.includes(factor.name)) && (
          <span className="badge warning" title="Add it to a block's design on the Blocks step to include it in trials">
            not in any block
          </span>
        )}
        <button className="small remove" title="Delete factor" onClick={remove}>×</button>
      </header>

      {factor.kind === "basic" ? (
        <div className="levels">
          {factor.levels.map((level, i) => (
            <span className="chip" key={`${i}-${level.name}`}>
              <span className="badge">level</span>
              <CommitInput value={String(level.name)}
                validate={nameTaken(levelNames.filter((n) => n !== level.name).map(String))}
                onCommit={(name) => onChange(renameLevel(model, factor.name, level.name, name))} />
              <Weight level={level} onChange={(weight) => updateLevel(i, { ...level, weight })} />
              <button className="small remove" title="Remove level"
                onClick={() => update({ ...factor, levels: factor.levels.filter((_, j) => j !== i) })}>×</button>
            </span>
          ))}
          <AddInput placeholder="+ level, then Enter"
            onAdd={(name) => !levelNames.includes(name) && update({ ...factor, levels: [...factor.levels, { name, weight: 1 }] })} />
        </div>
      ) : (
        <>
          <div className="derivation">
            <span>Based on</span>
            {factor.inputs!.map((name) => (
              <span className="chip" key={name}>
                {name}
                {factor.inputs!.length > 1 && (
                  <button className="small remove" onClick={() => setInputs(factor.inputs!.filter((n) => n !== name))}>×</button>
                )}
              </span>
            ))}
            <select value="" onChange={(e) => setInputs([...factor.inputs!, e.target.value])}>
              <option value="">+ factor</option>
              {earlier.filter((n) => !factor.inputs!.includes(n)).map((n) => <option key={n}>{n}</option>)}
            </select>
            <select value={factor.kind} onChange={(e) => update({ ...factor, kind: e.target.value as Kind })}>
              <option value="within">within the same trial</option>
              <option value="transition">compared with the previous trial</option>
            </select>
          </div>
          <div className="derived-levels">
            {factor.levels.map((level, i) => (
              <div className="derived-level" key={i}>
                <span className="level-name">
                  <span className="badge">level</span>
                  <CommitInput value={String(level.name)}
                    validate={nameTaken(levelNames.filter((n) => n !== level.name).map(String))}
                    onCommit={(name) => onChange(renameLevel(model, factor.name, level.name, name))} />
                  <Weight level={level} onChange={(weight) => updateLevel(i, { ...level, weight })} />
                </span>
                <select value={level.rule ? "when" : "otherwise"} onChange={(e) =>
                  updateLevel(i, { ...level, rule: e.target.value === "when" ? defaultRule(model, factor.inputs!) : null })}>
                  <option value="when">when</option>
                  <option value="otherwise">otherwise</option>
                </select>
                {level.rule ? (
                  <RuleEditor rule={level.rule} model={model} inputs={factor.inputs!} kind={factor.kind}
                    onChange={(rule) => updateLevel(i, { ...level, rule })} />
                ) : (
                  <span className="hint">no other level applies</span>
                )}
                <button className="small remove level-remove" title="Remove level"
                  onClick={() => update({ ...factor, levels: factor.levels.filter((_, j) => j !== i) })}>×</button>
              </div>
            ))}
          </div>
          <button className="small" onClick={() => update({ ...factor, levels: [...factor.levels,
            { name: uniqueName(levelNames, "level"), weight: 1, rule: defaultRule(model, factor.inputs!) }] })}>
            + level
          </button>
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
        Factors are what varies from trial to trial. A <strong>derived factor</strong> is computed from other
        factors.
      </p>
      {model.factors.map((_, i) => (
        <FactorCard key={i} model={model} index={i} onChange={onChange} />
      ))}
      <div className="add-bar">
        <button onClick={() => add({ name: uniqueName(names, "factor"), kind: "basic", levels: [] })}>
          + Factor
        </button>
        <button disabled={names.length === 0} title="A factor whose levels follow from other factors"
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
    </div>
  );
}
