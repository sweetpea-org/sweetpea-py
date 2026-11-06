import { Fragment, useEffect, useLayoutEffect, useRef, useState, type MouseEvent, type ReactNode } from "react";
import { HideButton } from "./Splitter";
import { crossingTitle, runs, type Block, type BlockSize, type Constraint, type Factor } from "../model";

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
  factors: Factor[];
  sizes: Record<string, BlockSize> | undefined;
  selected: string | null;
  onSelect: (name: string) => void;
  inside?: ReactNode;
  bands?: ReactNode[];
};

// The "link" outline icon from Tabler Icons (MIT): it marks a constraint.
function LinkIcon() {
  return (
    <svg className="d-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M9 15l6 -6" />
      <path d="M11 6l.463 -.536a5 5 0 0 1 7.071 7.072l-.534 .464" />
      <path d="M13 18l-.397 .534a5.068 5.068 0 0 1 -7.127 0a4.972 4.972 0 0 1 0 -7.071l.524 -.463" />
    </svg>
  );
}

function Tags({ block }: { block: Block }) {
  if (block.constraints.length === 0) return null;
  return (
    <span className="d-tags">
      {block.constraints.map((c, i) => <span key={i} className="d-tag" title="Constraint"><LinkIcon />{describe(c)}</span>)}
    </span>
  );
}

// More chips than this would crowd the frame; the rest are counted instead.
const MAX_CHIPS = 6;

/** The combinations an outer block runs, as chips: one per level of a single crossed factor,
 * or "morning × d1" style when it crosses several. */
function Combinations({ crossing, factors }: { crossing: string[]; factors: Factor[] }) {
  const levels = crossing.map((name) => (factors.find((f) => f.name === name)?.levels ?? []).map((l) => String(l.name)));
  const all = levels.reduce<string[]>((acc, names) => acc.flatMap((a) => names.map((n) => (a ? `${a} × ${n}` : n))), [""]);
  return (
    <span className="d-chips">
      {all.slice(0, MAX_CHIPS).map((c) => <span key={c} className="d-chip">{c}</span>)}
      {all.length > MAX_CHIPS && <span className="d-note">+{all.length - MAX_CHIPS} more</span>}
    </span>
  );
}

/** The structure drawn as what it means: a Nest's outer block frames its inner block, merged
 * blocks sit side by side joined by a junction, and a Repeat's arrow leaves its block and returns. */
function Diagram(props: DiagramProps) {
  const { block, factors, sizes, selected, onSelect, inside, bands = [] } = props;
  const pick = (e: MouseEvent) => {
    e.stopPropagation();
    onSelect(block.name);
  };
  const size = sizes?.[block.name];
  const mark = (base: string) => `${base}${block.name === selected ? " selected" : ""}`;
  const sub = (b: Block, within?: ReactNode) =>
    <Diagram key={b.name} block={b} factors={factors} sizes={sizes} selected={selected} onSelect={onSelect} inside={within} />;

  if (block.type === "nest") {
    // A Nest has no box: its outer block frames the inner one, and its band closes the outer frame.
    const band = (
      <div key={block.name} className={mark("d-band")} onClick={pick} role="button" tabIndex={0}>
        <span className="d-label">Nest · {block.name}{size ? ` · ${size.trials} trials` : ""}</span>
        <Tags block={block} />
      </div>
    );
    return <Diagram {...props} block={block.outer} inside={sub(block.inner, inside)} bands={[band, ...bands]} />;
  }

  const held = inside && <div className="d-held">{inside}</div>;

  if (block.type === "cross") {
    const ticks = size ? size.trials : 0;
    return (
      <div className={mark(inside ? "d-box d-frame" : "d-box")} onClick={pick} role="button" tabIndex={0}>
        {inside ? (
          // An outer block runs what it frames once for each of its combinations.
          <div className="d-head">
            <strong>{block.name}</strong>
            <Combinations crossing={block.crossings[0] ?? []} factors={factors} />
          </div>
        ) : (
          <div className="d-head">
            <strong>{block.name}</strong>
            <span className="d-note">{crossingTitle(block)}{size ? ` · ${size.trials} trials` : ""}</span>
          </div>
        )}
        {!inside && ticks > 0 && ticks <= MAX_TICKS && <div className="d-ticks" style={{ backgroundSize: `${100 / ticks}% 100%` }} />}
        <Tags block={block} />
        {held}
        {bands}
      </div>
    );
  }

  if (block.type === "merge") {
    return (
      <div className="d-merge">
        <div className="merge-row">
          {block.blocks.map((b, i) => (
            <Fragment key={b.name}>
              {i > 0 && (
                <div className={mark("merge-link")} onClick={pick} role="button" tabIndex={0} title={`Merge · ${block.name}`}>
                  <span className="merge-node">+</span>
                  <span className="d-note">merge</span>
                </div>
              )}
              {sub(b)}
            </Fragment>
          ))}
        </div>
        <div className={mark("merge-span")} onClick={pick} role="button" tabIndex={0}>
          <span className="d-label merge">Merge · {block.name}{size ? ` · ${size.trials} trials` : ""}</span>
          <Tags block={block} />
        </div>
        {held}
        {bands}
      </div>
    );
  }

  return (
    <div className="d-repeat">
      <div className={mark("loop-label")} onClick={pick} role="button" tabIndex={0}>
        <span>↻ repeat ×{runs(block, sizes) ?? "?"}</span>
        <Tags block={block} />
      </div>
      <div className="loop-area">
        {/* A circular arrow around the block's top-right corner, centred on the corner: it leaves
            the right edge, curves up and over, and points back down into the top. */}
        <svg className={mark("loop-arrow")} viewBox="0 0 52 52" onClick={pick} aria-label={`Repeat · ${block.name}`}>
          <title>{`Repeat · ${block.name}`}</title>
          <path d="M26 44 A18 18 0 1 0 8 26" fill="none" />
          <polygon points="3,19 13,19 8,28" />
        </svg>
        <div className="loop-body">{sub(block.block, inside)}</div>
      </div>
      {bands}
    </div>
  );
}

type Props = {
  block: Block;
  factors: Factor[];
  nodes: Record<string, BlockSize> | undefined;
  selected: string | null;
  onSelect: (name: string) => void;
  onHide?: () => void;
};

// Zoom steps when zooming in or out from the fitted size.
const ZOOM_STEP = 1.25;
const ZOOM_MIN = 0.25;
const ZOOM_MAX = 3;

/** Scales the diagram to fit the pane's width unless the user has zoomed; returns the scale
 * in use, the stage size it takes up, and refs for the scroller and the unscaled content. */
function useFit(zoom: number | null) {
  const scroller = useRef<HTMLDivElement>(null);
  const content = useRef<HTMLDivElement>(null);
  const [room, setRoom] = useState(0);
  const [natural, setNatural] = useState({ width: 0, height: 0 });
  // Transforms leave layout sizes alone, so the content keeps reporting its natural size.
  const measure = () => {
    const width = content.current!.offsetWidth;
    const height = content.current!.offsetHeight;
    setRoom(scroller.current!.clientWidth);
    setNatural((n) => (n.width === width && n.height === height ? n : { width, height }));
  };
  // After every render, so a new design fits at once; the observer covers the pane being resized.
  useLayoutEffect(measure);
  useEffect(() => {
    const observer = new ResizeObserver(measure);
    observer.observe(scroller.current!);
    return () => observer.disconnect();
  }, []);
  const fit = natural.width > 0 ? Math.min(1, (room - STAGE_PADDING) / natural.width) : 1;
  const scale = zoom ?? Math.max(ZOOM_MIN, fit);
  return { scroller, content, fit, scale, stage: { width: natural.width * scale, height: natural.height * scale } };
}

// The scroller's horizontal padding, which the fitted diagram stays inside.
const STAGE_PADDING = 24;

export default function StructurePane({ block, factors, nodes, selected, onSelect, onHide }: Props) {
  // null fits the diagram to the pane; a number is a zoom the user chose.
  const [zoom, setZoom] = useState<number | null>(null);
  const { scroller, content, fit, scale, stage } = useFit(zoom);
  // Each step starts from the zoom before it, so quick repeated clicks all count.
  const zoomBy = (factor: number) =>
    setZoom((z) => Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, (z ?? scale) * factor)));

  return (
    <aside className="tree-pane" data-view="Structure">
      <div className="tree-toolbar">
        <h2>Block structure</h2>
        <div className="zoom-controls" role="group" aria-label="Zoom">
          <button className="small" title="Zoom out" onClick={() => zoomBy(1 / ZOOM_STEP)}>−</button>
          <span className="zoom-level" aria-live="polite">{Math.round(scale * 100)}%</span>
          <button className="small" title="Zoom in" onClick={() => zoomBy(ZOOM_STEP)}>+</button>
          <button className={zoom === null ? "small on" : "small"} title="Fit the whole structure in the pane"
            onClick={() => setZoom(null)}>
            Fit
          </button>
        </div>
        <HideButton onHide={onHide} label="the block structure" />
      </div>
      <p className="hint">A frame runs its contents once for each of its levels (the chips); + joins merged blocks; ↻ repeats a
        block; <LinkIcon /> marks a constraint. Click a part to edit it.</p>
      <div className="tree-scroll structure" ref={scroller}>
        <div className="d-stage" style={{ width: stage.width, height: stage.height }}>
          <div className="d-root" ref={content} style={{ transform: `scale(${scale})` }}>
            <Diagram block={block} factors={factors} sizes={nodes} selected={selected} onSelect={onSelect} />
          </div>
        </div>
      </div>
      {zoom !== null && zoom > fit && <p className="hint zoom-note">Zoomed in · scroll to see the rest, or press Fit</p>}
    </aside>
  );
}
