import type { MouseEvent, ReactNode } from "react";
import { HideButton } from "./Splitter";
import { crossingTitle, runs, type Block, type BlockSize, type Constraint } from "../model";

// Above this many trials, ticks would be thinner than a pixel.
const MAX_TICKS = 120;

/** A constraint in a few words, such as "session in order". */
function describe(c: Constraint): string {
  const ref = c.level === null || c.level === undefined ? c.factor : `${c.factor} = ${c.level}`;
  const factors = (c.factors ?? []).join(", ");
  switch (c.type) {
    case "AtMostKInARow": return `at most ${c.k} in a row: ${ref}`;
    case "AtLeastKInARow": return `at least ${c.k} in a row: ${ref}`;
    case "ExactlyKInARow": return `exactly ${c.k} in a row: ${ref}`;
    case "ExactlyK": return `exactly ${c.k} times: ${ref}`;
    case "Exclude": return `never ${ref}`;
    case "Pin": return `trial ${c.index} is ${ref}`;
    case "MinimumTrials": return `at least ${c.trials} trials`;
    case "Sequential": return `${c.factor} in order`;
    case "LatinSquare": return `Latin square of ${factors}`;
    default: return `cover all combinations of ${factors}`;
  }
}

type DiagramProps = {
  block: Block;
  sizes: Record<string, BlockSize> | undefined;
  selected: string | null;
  onSelect: (name: string) => void;
  inside?: ReactNode;
  bands?: ReactNode[];
};

function Constraints({ block }: { block: Block }) {
  if (block.constraints.length === 0) return null;
  return <ul className="d-constraints">{block.constraints.map((c, i) => <li key={i}>{describe(c)}</li>)}</ul>;
}

/** The structure drawn as what it means: a Nest's outer block contains its inner block, a Merge
 * stacks tracks over the same trials, and a Repeat is a stack of copies. */
function Diagram(props: DiagramProps) {
  const { block, sizes, selected, onSelect, inside, bands = [] } = props;
  const pick = (e: MouseEvent) => {
    e.stopPropagation();
    onSelect(block.name);
  };
  const size = sizes?.[block.name];
  const mark = (base: string) => `${base}${block.name === selected ? " selected" : ""}`;
  const sub = (b: Block, within?: ReactNode) =>
    <Diagram key={b.name} block={b} sizes={sizes} selected={selected} onSelect={onSelect} inside={within} />;

  if (block.type === "nest") {
    // A Nest has no box: its outer block holds the inner one, and its band closes the outer frame.
    const band = (
      <div key={block.name} className={mark("d-band")} onClick={pick} role="button" tabIndex={0}>
        <span className="d-label">Nest · {block.name}{size ? ` · ${size.trials} trials` : ""}</span>
        <span className="d-note">across all trials</span>
        <Constraints block={block} />
      </div>
    );
    return <Diagram {...props} block={block.outer} inside={sub(block.inner, inside)} bands={[band, ...bands]} />;
  }

  const held = inside && (
    <div className="d-held">
      <span className="d-note">held constant for each run of</span>
      {inside}
    </div>
  );

  if (block.type === "cross") {
    const ticks = size ? size.trials : 0;
    return (
      <div className={mark("d-box d-cross")} onClick={pick} role="button" tabIndex={0}>
        <div className="d-head">
          <strong>{crossingTitle(block)}</strong>
          <span className="d-note">{block.name}{size ? ` · ${size.trials} ${inside ? "combinations" : "trials"}` : ""}</span>
        </div>
        {ticks > 0 && ticks <= MAX_TICKS && <div className="d-ticks" style={{ backgroundSize: `${100 / ticks}% 100%` }} />}
        <Constraints block={block} />
        {held}
        {bands}
      </div>
    );
  }

  if (block.type === "merge") {
    return (
      <div className={mark("d-box d-merge")} onClick={pick} role="button" tabIndex={0}>
        <div className="d-head">
          <strong>Merge</strong>
          <span className="d-note">{block.name}{size ? ` · ${size.trials} trials` : ""}</span>
        </div>
        <div className="d-tracks">{block.blocks.map((b) => sub(b))}</div>
        {held}
        {block.constraints.length > 0 && (
          <div className="d-band d-own"><span className="d-note">across all trials</span><Constraints block={block} /></div>
        )}
        {bands}
      </div>
    );
  }

  return (
    <div className={mark("d-box d-repeat")} onClick={pick} role="button" tabIndex={0}>
      <div className="d-head">
        <strong>Repeat ×{runs(block, sizes) ?? "?"}</strong>
        <span className="d-note">{block.name}{size ? ` · ${size.trials} trials` : ""}</span>
      </div>
      {sub(block.block, inside)}
      {block.constraints.length > 0 && (
        <div className="d-band d-own"><span className="d-note">across runs</span><Constraints block={block} /></div>
      )}
      {bands}
    </div>
  );
}

type Props = {
  block: Block;
  nodes: Record<string, BlockSize> | undefined;
  selected: string | null;
  onSelect: (name: string) => void;
  onHide?: () => void;
};

export default function StructurePane({ block, nodes, selected, onSelect, onHide }: Props) {
  return (
    <aside className="tree-pane" data-view="Structure">
      <div className="tree-toolbar">
        <h2>Block structure</h2>
        <HideButton onHide={onHide} label="the block structure" />
      </div>
      <p className="hint">Boxes inside a box run once per trial of the outer box. Click a part to edit it.</p>
      <div className="tree-scroll structure">
        <Diagram block={block} sizes={nodes} selected={selected} onSelect={onSelect} />
      </div>
    </aside>
  );
}
