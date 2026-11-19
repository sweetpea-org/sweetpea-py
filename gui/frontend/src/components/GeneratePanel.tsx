import { useState } from "react";
import { api, type Row } from "../api";
import { SAMPLERS, type Check, type Model } from "../model";
import { download } from "./FileMenu";

type Props = {
  model: Model;
  check: Check;
  onChange: (model: Model) => void;
  onSample: (rows: Row[] | null) => void;
};
type Result = { sequences: Row[][]; log: string; columns: string[] };

const cell = (value: unknown) => {
  const text = value === null || value === undefined ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
};

function toCsv(columns: string[], sequences: Row[][]): string {
  const header = ["sequence", "trial", ...columns].map(cell).join(",");
  const rows = sequences.flatMap((rows, s) =>
    rows.map((row, t) => [s + 1, t + 1, ...columns.map((c) => row[c])].map(cell).join(",")));
  return [header, ...rows].join("\n") + "\n";
}

// How each sampler chooses sequences, from SweetPea's sampling strategies.
const SAMPLER_HELP: Record<string, string> = {
  CMSGen: "CMSGen: close to uniformly random; two sequences may come out the same. A good default.",
  IterateGen: "IterateGen: every sequence is different, but they may not be uniformly random.",
  RandomGen: "RandomGen: uniformly random and all different; can be slow, or find nothing, when constraints are tight.",
};

export default function GeneratePanel({ model, check, onChange, onSample }: Props) {
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [shown, setShown] = useState(0);

  async function generate() {
    setRunning(true);
    setError(null);
    try {
      const sampled = await api.synthesize(model);
      if ("error" in sampled) {
        setError(sampled.error);
      } else {
        // Only factors in some block's design appear in the trials.
        const first = sampled.sequences[0]?.[0] ?? {};
        setResult({ ...sampled, columns: model.factors.map((f) => f.name).filter((n) => n in first) });
        onSample(sampled.sequences[0] ?? null);
      }
      setShown(0);
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(false);
    }
  }

  // Per-level colouring, kept for later: the table alternates two row shades instead, because
  // colouring by position confuses factors whose levels are themselves colours.
  // const levelClass = (column: string, value: unknown) => {
  //   const index = findFactor(model, column)?.levels.findIndex((l) => l.name === value) ?? -1;
  //   return index < 0 ? undefined : `lv lv${index % 8}`;
  // };

  const rows = result?.sequences[shown] ?? [];

  return (
    <div className="generate-panel">
      <div className="card fields">
        <label title="How many trial sequences to generate, for example one per participant">
          Sequences
          <input type="number" min={1} value={model.samples}
            onChange={(e) => onChange({ ...model, samples: Math.max(1, Math.round(Number(e.target.value)) || 1) })} />
        </label>
        <label title={SAMPLER_HELP[model.sampler]}>
          Sampler
          <select value={model.sampler} onChange={(e) => onChange({ ...model, sampler: e.target.value })}>
            {SAMPLERS.map((s) => <option key={s} title={SAMPLER_HELP[s]}>{s}</option>)}
          </select>
        </label>
        <button className="primary" disabled={running || !!check.error} onClick={generate}
          title={check.error ? "Fix the design's problem first" : "Run the solver and show the sequences"}>
          {running ? "Generating…" : "Generate"}
        </button>
        {result && result.sequences.length > 0 && (
          <button title="Save every sequence in one CSV file, with sequence and trial numbers"
            onClick={() => download("experiment.csv", toCsv(result.columns, result.sequences), "text/csv")}>
            Download CSV
          </button>
        )}
      </div>

      {error && <div className="banner error">{error}</div>}

      {result && (
        <>
          {result.sequences.length === 0 ? (
            <div className="banner warning">The solver found no answer (UNSAT). Try changing the design, for example by loosening or removing a constraint. The solver’s report is below.</div>
          ) : (
            <div className="sequence-tabs">
              {result.sequences.map((_, i) => (
                <button key={i} className={i === shown ? "step active" : "step"} title="Show this sequence" onClick={() => setShown(i)}>
                  Sequence {i + 1}
                </button>
              ))}
            </div>
          )}
          {rows.length > 0 && (
            <div className="table-scroll">
              <table className="trials">
                <thead>
                  <tr>
                    <th>#</th>
                    {result.columns.map((c) => <th key={c}>{c}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, t) => (
                    <tr key={t}>
                      <td className="hint">{t + 1}</td>
                      {result.columns.map((c) => (
                        <td key={c}>{row[c] ?? "—"}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <details className="log">
            <summary title="What SweetPea printed while generating">Solver report</summary>
            <pre>{result.log}</pre>
          </details>
        </>
      )}
    </div>
  );
}
