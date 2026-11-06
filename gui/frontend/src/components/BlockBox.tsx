import { useEffect, useRef, type MouseEvent, type ReactNode } from "react";
import {
  BLOCK_LABELS, blockNameProblem, crossingTitle, newLeaf, runs, uniqueBlockName, unwrapBlock, updateBlock, wrapBlock,
  type Alignment, type Block, type Check, type LeafBlock, type Mode, type Model, type Wrapper,
} from "../model";
import CommitInput from "./CommitInput";
import { ConstraintList, scopeNote } from "./ConstraintsPanel";

type Props = { model: Model; check: Check; onChange: (model: Model) => void };

const MODES: Record<Mode, string> = {
  repeat: "repeat — each combination once per run of the crossing",
  weight: "weight — combinations may repeat anywhere",
  equal: "equal — crossings must be the same size",
};
const ALIGNMENTS: Record<Alignment, string> = {
  "equal preamble": "equal preamble — crossings need the same preamble",
  "post preamble": "post preamble — all crossings start after the longest preamble",
  "parallel start": "parallel start — each crossing starts after its own preamble",
};

function Advanced({ block, onChange }: { block: Block; onChange: (b: Block) => void }) {
  if (block.type === "repeat") return null;
  const option = (value: string | null, label: string) => <option key={label} value={value ?? ""}>{label}</option>;
  return (
    <details className="advanced">
      <summary>Advanced</summary>
      {"mode" in block && (
        <label>
          Smaller crossings fill extra trials by
          <select value={block.mode ?? ""} onChange={(e) => onChange({ ...block, mode: (e.target.value || null) as Mode | null })}>
            {option(null, "default")}
            {Object.entries(MODES).map(([value, label]) => option(value, label))}
          </select>
        </label>
      )}
      <label>
        Preamble alignment
        <select value={block.alignment ?? ""}
          onChange={(e) => onChange({ ...block, alignment: (e.target.value || null) as Alignment | null })}>
          {option(null, "default")}
          {Object.entries(ALIGNMENTS).map(([value, label]) => option(value, label))}
        </select>
      </label>
    </details>
  );
}

function LeafBody({ model, block, onChange }: Props & { block: LeafBlock }) {
  const set = (b: LeafBlock) => onChange({ ...model, block: updateBlock(model.block, block.name, () => b) });
  const toggleDesign = (name: string) => set(block.design.includes(name)
    ? { ...block, design: block.design.filter((n) => n !== name), crossings: block.crossings.map((c) => c.filter((n) => n !== name)) }
    : { ...block, design: [...block.design, name] });
  const toggleCrossed = (i: number, name: string) => {
    const crossing = block.crossings[i];
    const next = crossing.includes(name) ? crossing.filter((n) => n !== name) : [...crossing, name];
    // A crossed factor must be in the block's design.
    set({ ...block, design: block.design.includes(name) ? block.design : [...block.design, name],
          crossings: block.crossings.map((c, j) => (j === i ? next : c)) });
  };
  const size = (crossing: string[]) => crossing.reduce((n, name) =>
    n * (model.factors.find((f) => f.name === name)?.levels.reduce((w, l) => w + l.weight, 0) ?? 0), 1);

  return (
    <>
      <div className="field-row">
        <span className="field-label" title="Factors that get a level on every trial of this block">Design</span>
        <span className="checks">
          {model.factors.map((f) => (
            <label key={f.name} className="check">
              <input type="checkbox" checked={block.design.includes(f.name)} onChange={() => toggleDesign(f.name)} />
              {f.name}
            </label>
          ))}
        </span>
      </div>
      {block.crossings.map((crossing, i) => (
        <div className="field-row" key={i}>
          <span className="field-label" title="Every combination of these factors' levels appears in each run">
            Crossing{block.crossings.length > 1 ? ` ${i + 1}` : ""}
          </span>
          <span className="checks">
            {model.factors.map((f) => (
              <label key={f.name} className="check">
                <input type="checkbox" checked={crossing.includes(f.name)} onChange={() => toggleCrossed(i, f.name)} />
                {f.name}
              </label>
            ))}
          </span>
          <span className="hint">{crossing.length ? `${size(crossing)} combinations` : "nothing crossed"}</span>
          {block.crossings.length > 1 && (
            <button className="small remove" title="Remove crossing"
              onClick={() => set({ ...block, crossings: block.crossings.filter((_, j) => j !== i) })}>×</button>
          )}
        </div>
      ))}
      <div className="field-row">
        <button className="small" title="Cross another set of factors independently in the same trials"
          onClick={() => set({ ...block, crossings: [...block.crossings, []] })}>+ crossing</button>
        <label className="check" title="Turn off when constraints exclude some combinations">
          <input type="checkbox" checked={block.requireCompleteCrossing}
            onChange={(e) => set({ ...block, requireCompleteCrossing: e.target.checked })} />
          every combination must appear
        </label>
      </div>
    </>
  );
}

export type Selection = { selected: string | null; onSelect: (name: string) => void };

type BoxProps = Props & Selection & {
  block: Block;
  /** Drawn inside this block's frame: the inner block of a Nest this block is the outer of. */
  inside?: ReactNode;
  /** Bands of the Nests whose outer frame this block draws; they sit at the bottom of the frame. */
  bands?: ReactNode[];
  onRemove?: () => void;
};

/** Scrolls an element into view when its block becomes selected. */
function useSelection(name: string, selected: string | null) {
  const ref = useRef<HTMLDivElement>(null);
  const isSelected = name === selected;
  useEffect(() => {
    if (isSelected) ref.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [isSelected]);
  return { ref, isSelected };
}

/** Name, trial count, the Arrange… menu and, in a Merge, the remove button. */
function Controls({ model, check, onChange, block, onSelect, selected, onRemove, inside }: BoxProps) {
  const trials = check.nodes?.[block.name]?.trials;
  const canUnwrap = block.type === "nest" || block.type === "repeat" || (block.type === "merge" && block.blocks.length === 1);

  function act(action: string) {
    if (action === "unwrap") onChange({ ...model, block: unwrapBlock(model.block, block.name) });
    else onChange({ ...model, block: wrapBlock(model, block.name, action as Wrapper, trials ?? 0) });
  }

  return (
    <>
      <CommitInput className="block-name" value={block.name}
        validate={(name) => blockNameProblem(model, name, block.name)}
        onCommit={(name) => {
          onChange({ ...model, block: updateBlock(model.block, block.name, () => ({ ...block, name })) });
          if (selected === block.name) onSelect(name);
        }} />
      {trials !== undefined && (
        // An outer block's trials are combinations, each held for a run of what it contains.
        <span className="trials">{trials} {block.type === "cross" && inside ? "combinations" : "trials"}</span>
      )}
      <select className="actions" value="" onChange={(e) => act(e.target.value)}>
        <option value="">Arrange…</option>
        <option value="nest">Nest inside a new outer block</option>
        <option value="merge">Merge with other blocks</option>
        <option value="repeat">Repeat</option>
        {canUnwrap && <option value="unwrap">Remove this {BLOCK_LABELS[block.type]} (keep what's inside)</option>}
      </select>
      {onRemove && <button className="small remove" title="Remove from the merge" onClick={onRemove}>×</button>}
    </>
  );
}

/** A container's own settings and constraints, along the bottom of the frame it belongs to. */
function Band(props: BoxProps & { label: string; withControls: boolean }) {
  const { model, block, onChange, selected, onSelect, label, withControls } = props;
  // A Merge or Repeat frame shows its own selection, so only a Nest's band does.
  const { ref, isSelected } = useSelection(block.name, withControls ? selected : null);
  const setBlock = (b: Block) => onChange({ ...model, block: updateBlock(model.block, block.name, () => b) });
  return (
    <div ref={ref} className={`frame-band band-${block.type}${isSelected ? " selected" : ""}`}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(block.name);
      }}>
      <div className="block-header">
        <span className="badge block-badge">{label}</span>
        {withControls && <Controls {...props} onRemove={undefined} />}
      </div>
      <span className="hint">{scopeNote(block)}</span>
      <ConstraintList model={model} block={block} onChange={onChange} />
      <Advanced block={block} onChange={setBlock} />
    </div>
  );
}

/** Edits a block drawn as what it means: a Nest's outer block contains its inner block, a
 * Merge stacks its blocks as tracks over the same trials, and a Repeat is a stack of copies. */
export default function BlockBox(props: BoxProps) {
  const { model, check, onChange, block, inside, bands = [], selected, onSelect } = props;
  const { ref, isSelected } = useSelection(block.name, selected);
  const setBlock = (b: Block) => onChange({ ...model, block: updateBlock(model.block, block.name, () => b) });
  const select = (e: MouseEvent) => {
    e.stopPropagation();
    onSelect(block.name);
  };
  const sel = { selected, onSelect };

  if (block.type === "nest") {
    // A Nest has no frame of its own: its outer block's frame holds the inner block and, at the
    // bottom, the Nest's band.
    const band = <Band key={block.name} {...props} label="Nest · across all trials" withControls />;
    const inner = <BlockBox model={model} check={check} onChange={onChange} block={block.inner} inside={inside} {...sel} />;
    return <BlockBox {...props} block={block.outer} inside={inner} bands={[band, ...bands]} />;
  }

  const frameClass = `block-box block-${block.type}${isSelected ? " selected" : ""}`;

  if (block.type === "cross") {
    return (
      <article ref={ref} className={frameClass}>
        <header className="block-header" onClick={select}>
          <span className="crossing-title">{crossingTitle(block)}</span>
          <Controls {...props} />
        </header>
        <LeafBody model={model} check={check} onChange={onChange} block={block} />
        <Advanced block={block} onChange={setBlock} />
        <div className="block-constraints">
          <span className="field-label">Constraints</span>
          <span className="hint">{scopeNote(block)}</span>
          <ConstraintList model={model} block={block} onChange={onChange} />
        </div>
        {inside && (
          <div className="held">
            <span className="held-note">Held constant for each run of:</span>
            {inside}
          </div>
        )}
        {bands}
      </article>
    );
  }

  if (block.type === "merge") {
    const remove = (i: number) => () => setBlock({ ...block, blocks: block.blocks.filter((_, j) => j !== i) });
    return (
      <article ref={ref} className={frameClass}>
        <header className="block-header" onClick={select}>
          <span className="frame-title">Merge</span>
          <Controls {...props} />
        </header>
        <p className="hint">These blocks run over the same trials.</p>
        <div className="merge-tracks">
          {block.blocks.map((b, i) => (
            <BlockBox key={b.name} model={model} check={check} onChange={onChange} block={b} {...sel}
              onRemove={block.blocks.length > 1 ? remove(i) : undefined} />
          ))}
        </div>
        <button className="small" onClick={() =>
          setBlock({ ...block, blocks: [...block.blocks, newLeaf(uniqueBlockName(model, "track"))] })}>
          + block
        </button>
        {inside && <div className="held"><span className="held-note">Held constant for each run of:</span>{inside}</div>}
        <Band {...props} label="Merge · across all trials" withControls={false} />
        {bands}
      </article>
    );
  }

  return (
    <article ref={ref} className={`${frameClass} repeat-deck`}>
      <header className="block-header" onClick={select}>
        <span className="frame-title">Repeat</span>
        <span className="runs-badge">×{runs(block, check.nodes) ?? "?"}</span>
        <Controls {...props} />
      </header>
      <BlockBox model={model} check={check} onChange={onChange} block={block.block} inside={inside} {...sel} />
      <Band {...props} label="Repeat · across runs" withControls={false} />
      {bands}
    </article>
  );
}
