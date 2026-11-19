import type { Row as Trial } from "../api";
import type { Block, BlockSize } from "../model";

/** A stretch of the sequence: one run of a block (with a tick per trial), or
 * one trial of an outer block held constant across ``unit`` trials. */
type Segment = { start: number; length: number; ticks: number; preamble: number; held: number | null };
type Row = { name: string; label: string; factors: string[]; segments: Segment[] };

// Above this many trials, ticks would be thinner than a pixel.
const MAX_TICKS = 200;

/** Adds the rows for ``block`` drawn from trial ``start`` up to ``end``, where
 * each of the block's trials covers ``unit`` trials of the whole sequence.
 * Returns how many trials of the sequence the block covers. */
function layout(block: Block, nodes: Record<string, BlockSize>, rows: Map<string, Row>,
                start: number, end: number, unit: number, withPreamble: boolean): number {
  const size = nodes[block.name] ?? { trials: 0, preamble: 0 };
  const trials = withPreamble ? size.trials : size.trials - size.preamble;

  if (block.type === "cross") {
    const row = rows.get(block.name) ?? { name: block.name, label: block.crossings.map((c) => c.join(" × ")).join("  +  "),
                                          factors: block.crossings.flat(), segments: [] };
    rows.set(block.name, row);
    const preamble = withPreamble ? size.preamble : 0;
    if (unit === 1) {
      const length = Math.min(trials, end - start);
      if (length > 0) row.segments.push({ start, length, ticks: length, preamble, held: null });
    } else {
      for (let i = 0; i < trials && start + i * unit < end; i++) {
        row.segments.push({ start: start + i * unit, length: Math.min(unit, end - start - i * unit),
                            ticks: 0, preamble: 0, held: i });
      }
    }
    return trials * unit;
  }

  if (block.type === "nest") {
    // Each trial of the outer block lasts one run of the inner block, preamble excluded.
    const inner = nodes[block.inner.name] ?? { trials: 0, preamble: 0 };
    const run = (inner.trials - inner.preamble) * unit;
    const span = layout(block.outer, nodes, rows, start, end, run, withPreamble);
    for (let s = start; s < Math.min(start + span, end); s += run) {
      layout(block.inner, nodes, rows, s, Math.min(s + run, end), unit, false);
    }
    return span;
  }

  // Merge and Repeat run each block they contain over and over to fill their own length.
  const stop = Math.min(start + trials * unit, end);
  for (const child of block.type === "merge" ? block.blocks : [block.block]) {
    for (let s = start, first = withPreamble; s < stop; first = false) {
      const covered = layout(child, nodes, rows, s, stop, unit, first);
      if (covered <= 0) break;
      s += covered;
    }
  }
  return trials * unit;
}

type Props = { block: Block; nodes: Record<string, BlockSize> | undefined; sample: Trial[] | null };

export default function Timeline({ block, nodes, sample }: Props) {
  if (!nodes) return null;
  const total = nodes[block.name]?.trials ?? 0;
  if (total === 0) return null;
  const rows = new Map<string, Row>();
  layout(block, nodes, rows, 0, total, 1, true);
  const pct = (n: number) => `${(n / total) * 100}%`;

  // Before generation a held trial shows its position; after, the levels it held in sequence 1.
  const heldLabel = (row: Row, seg: Segment) =>
    sample?.[seg.start] ? row.factors.map((f) => sample[seg.start][f]).join(" · ") : `#${seg.held! + 1}`;

  return (
    <div className="timeline card">
      <div className="timeline-head">
        <h3>Timeline</h3>
        <span className="hint">
          {total} trials per sequence · each row is a block’s crossing; boxes inside a box run once per outer trial
          {sample ? " · labels from sequence 1" : ""}
        </span>
      </div>
      {[...rows.values()].map((row) => (
        <div className="timeline-row" key={row.name}>
          <div className="timeline-label" title={row.name}>
            <span>{row.label || "(no crossing)"}</span>
            <span className="hint">{row.name}</span>
          </div>
          <div className="timeline-track">
            {row.segments.map((seg, i) => (
              <div key={i} style={{ left: pct(seg.start), width: pct(seg.length) }}
                className={seg.held === null ? "seg run" : `seg held shade-${seg.held % 2}`}
                title={seg.held === null ? `${seg.length} trials` : `held for ${seg.length} trials`}>
                {seg.held !== null && <span>{heldLabel(row, seg)}</span>}
                {seg.held === null && total <= MAX_TICKS && (
                  <div className="ticks" style={{ backgroundSize: `${100 / seg.ticks}% 100%` }} />
                )}
                {seg.preamble > 0 && <div className="preamble" style={{ width: `${(seg.preamble / seg.length) * 100}%` }}
                  title={`${seg.preamble} preamble trials`} />}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
