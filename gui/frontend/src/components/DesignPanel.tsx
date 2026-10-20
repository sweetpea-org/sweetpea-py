import { type Check, type Model } from "../model";

type Props = { model: Model; check: Check; onChange: (model: Model) => void };

export default function DesignPanel({ model, check, onChange }: Props) {
  const crossed = model.factors.filter((f) => model.crossing.includes(f.name));
  const combinations = crossed.reduce((n, f) => n * f.levels.reduce((w, l) => w + l.weight, 0), 1);

  function toggle(name: string) {
    const crossing = model.crossing.includes(name)
      ? model.crossing.filter((n) => n !== name)
      : model.factors.map((f) => f.name).filter((n) => n === name || model.crossing.includes(n));
    onChange({ ...model, crossing });
  }

  return (
    <div className="design-panel">
      <p className="intro">
        <strong>Crossed</strong> factors are counterbalanced: every combination of their levels appears equally
        often in each sequence. The other factors follow from the crossed ones or vary freely.
      </p>
      <div className="card">
        <h3>Crossing</h3>
        <div className="crossing-list">
          {model.factors.map((f) => (
            <label key={f.name} className="check">
              <input type="checkbox" checked={model.crossing.includes(f.name)} onChange={() => toggle(f.name)} />
              {f.name} <span className="hint">({f.levels.length} levels)</span>
            </label>
          ))}
        </div>
        <p className="formula">
          {crossed.length === 0 ? "Choose at least one factor to cross."
            : `${crossed.map((f) => `${f.name} (${f.levels.reduce((w, l) => w + l.weight, 0)})`).join(" × ")} = ${combinations} combinations`}
          {check.trials !== undefined && <> → <strong>{check.trials} trials</strong> per sequence</>}
        </p>
        <label className="check">
          <input type="checkbox" checked={model.requireCompleteCrossing}
            onChange={(e) => onChange({ ...model, requireCompleteCrossing: e.target.checked })} />
          Every combination must appear (turn off when constraints exclude some combinations)
        </label>
      </div>
    </div>
  );
}
