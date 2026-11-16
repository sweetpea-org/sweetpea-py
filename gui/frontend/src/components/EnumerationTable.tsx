import { enumerationKeys, enumerationRows, keyLabel, sameRow } from "../conditions";
import type { Factor, Model, Value } from "../model";

type Props = { factor: Factor; model: Model; onChange: (factor: Factor) => void };

/** One row per combination of the inputs' levels, each assigned to a level of the factor. */
export default function EnumerationTable({ factor, model, onChange }: Props) {
  const keys = enumerationKeys(factor);
  const rows = enumerationRows(factor, model);
  const owner = (row: Value[]) => factor.levels.findIndex((l) => (l.combos ?? []).some((c) => sameRow(c, row)));

  function assign(row: Value[], level: number) {
    onChange({
      ...factor,
      levels: factor.levels.map((l, i) => {
        const rest = (l.combos ?? []).filter((c) => !sameRow(c, row));
        return { ...l, combos: i === level ? [...rest, row] : rest };
      }),
    });
  }

  return (
    <table className="enumeration">
      <thead>
        <tr>
          {keys.map((k) => <th key={`${k.factor}${k.at}`}>{keyLabel(k, factor)}</th>)}
          <th>{factor.name}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => {
          const level = owner(row);
          return (
            <tr key={JSON.stringify(row)} className={level < 0 ? "unassigned" : undefined}>
              {row.map((v, i) => <td key={i}>{v}</td>)}
              <td>
                <select value={level} title="The level of this factor for this combination"
                  onChange={(e) => assign(row, Number(e.target.value))}>
                  <option value={-1}>None (never occurs)</option>
                  {factor.levels.map((l, i) => <option key={String(l.name)} value={i}>{l.name}</option>)}
                </select>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
