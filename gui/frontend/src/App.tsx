import { Fragment, useEffect, useRef, useState, type CSSProperties } from "react";
import { api, type Row } from "./api";
import { STARTER, type Check, type Model } from "./model";
import StructurePane from "./components/StructurePane";
import Splitter, { HideButton } from "./components/Splitter";
import CodePane, { type CodeError } from "./components/CodePane";
import ConstraintsPanel from "./components/ConstraintsPanel";
import BlocksPanel from "./components/BlocksPanel";
import FactorsPanel from "./components/FactorsPanel";
import GeneratePanel from "./components/GeneratePanel";

const STEPS = ["Factors", "Blocks", "Constraints", "Generate"] as const;
type Step = (typeof STEPS)[number];

// How long typing in the code pane pauses before the GUI catches up.
const PARSE_DELAY_MS = 400;

const VIEWS = ["Designer", "Structure", "Code"] as const;
type View = (typeof VIEWS)[number];
type Sizes = Record<View, number>;

// Visible views split the width in proportion to their sizes; equal sizes give equal shares.
const EQUAL: Sizes = { Designer: 1, Structure: 1, Code: 1 };

// Narrowest a view may be dragged.
const VIEW_MIN = 220;

export default function App() {
  const [model, setModel] = useState<Model>(STARTER);
  const [code, setCode] = useState("");
  const [check, setCheck] = useState<Check>({});
  const [codeError, setCodeError] = useState<CodeError | null>(null);
  const [step, setStep] = useState<Step>("Factors");
  const [selected, setSelected] = useState<string | null>(null);
  const [shown, setShown] = useState<View[]>([...VIEWS]);
  const [sizes, setSizes] = useState<Sizes>(EQUAL);

  // Showing or hiding a view shares the width equally among the views left.
  function showView(view: View, on: boolean) {
    const next = VIEWS.filter((v) => (v === view ? on : shown.includes(v)));
    if (next.length === 0) return;
    setShown(next);
    setSizes(EQUAL);
  }

  // The last visible view stays, so its Hide button is disabled.
  const hide = (view: View) => (shown.length > 1 ? () => showView(view, false) : undefined);

  /** Starts dragging the handle between two neighbouring views. */
  function startResize(left: View, right: View) {
    const width = (v: View) => document.querySelector(`[data-view="${v}"]`)!.getBoundingClientRect().width;
    // Sizes taken as pixel widths keep every other view where it is.
    const start = { ...sizes, ...Object.fromEntries(shown.map((v) => [v, width(v)])) } as Sizes;
    const pair = start[left] + start[right];
    return (dx: number) => {
      const leftWidth = Math.max(VIEW_MIN, Math.min(pair - VIEW_MIN, start[left] + dx));
      setSizes({ ...start, [left]: leftWidth, [right]: pair - leftWidth });
    };
  }

  // Choosing a block in the structure opens it for editing.
  function selectBlock(name: string) {
    setSelected(name);
    setStep("Blocks");
    if (!shown.includes("Designer")) showView("Designer", true);
  }
  // The first generated sequence, which labels the timeline until the design changes.
  const [sample, setSample] = useState<Row[] | null>(null);
  // Only the newest request may update the page; an older one finishing late is ignored.
  const latest = useRef(0);
  const parseTimer = useRef<number>();

  async function render(next: Model) {
    const id = ++latest.current;
    const rendered = await api.render(next);
    if (id !== latest.current) return;
    setCode(rendered.code);
    setCheck(rendered.check);
    setCodeError(null);
  }

  async function parse(text: string) {
    const id = ++latest.current;
    const parsed = await api.parse(text);
    if (id !== latest.current) return;
    if ("error" in parsed) {
      setCodeError(parsed);
    } else {
      setModel(parsed.model);
      setSample(null);
      setCheck(parsed.check);
      setCodeError(null);
    }
  }

  function editModel(next: Model) {
    window.clearTimeout(parseTimer.current);
    setModel(next);
    setSample(null);
    render(next);
  }

  function editCode(text: string) {
    setCode(text);
    window.clearTimeout(parseTimer.current);
    parseTimer.current = window.setTimeout(() => parse(text), PARSE_DELAY_MS);
  }

  useEffect(() => {
    render(STARTER);
  }, []);

  const panels: Record<Step, JSX.Element> = {
    Factors: <FactorsPanel model={model} onChange={editModel} />,
    Blocks: <BlocksPanel model={model} check={check} sample={sample} onChange={editModel}
      selected={selected} onSelect={setSelected} />,
    Constraints: <ConstraintsPanel model={model} onChange={editModel} />,
    Generate: <GeneratePanel model={model} check={check} onChange={editModel} onSample={setSample} />,
  };

  const views: Record<View, JSX.Element> = {
    Designer: (
      <section className="panel" data-view="Designer">
        <div className="pane-toolbar">
          <h2>Designer</h2>
          <HideButton onHide={hide("Designer")} label="the designer" />
        </div>
        {check.error && !codeError && <div className="banner error">{check.error}</div>}
        {codeError && (
          <div className="banner warning">
            The code can’t be shown in the designer
            {codeError.line ? ` (line ${codeError.line})` : ""}: {codeError.error}.{" "}
            <button className="link" onClick={() => render(model)}>
              Restore the code from the designer
            </button>
          </div>
        )}
        <fieldset disabled={codeError !== null}>{panels[step]}</fieldset>
      </section>
    ),
    Structure: <StructurePane block={model.block} nodes={check.nodes} selected={selected} onSelect={selectBlock}
      onHide={hide("Structure")} />,
    Code: <CodePane code={code} error={codeError} onChange={editCode} onHide={hide("Code")} />,
  };

  return (
    <div className="app">
      <header className="topbar">
        <h1>SweetPea Designer</h1>
        <nav className="steps">
          {STEPS.map((s, i) => (
            <button key={s} className={s === step ? "step active" : "step"} onClick={() => setStep(s)}>
              <span className="step-number">{i + 1}</span> {s}
            </button>
          ))}
        </nav>
        {/* Shown here too, since the designer that explains the problem may be hidden. */}
        {check.error && <div className="status error">Design has a problem</div>}
        <div className="views">
          <span className="views-label">Show / hide panes:</span>
          <div className="view-toggles" role="group" aria-label="Show or hide panes">
            {VIEWS.map((v) => (
              <button key={v} className={shown.includes(v) ? "view-toggle on" : "view-toggle"} aria-pressed={shown.includes(v)}
                disabled={shown.length === 1 && shown[0] === v}
                title={shown.length === 1 && shown[0] === v ? "The last visible pane can't be hidden"
                  : shown.includes(v) ? `Click to hide the ${v} pane` : `Click to show the ${v} pane`}
                onClick={() => showView(v, !shown.includes(v))}>
                <span className="view-check" aria-hidden>{shown.includes(v) ? "✓" : ""}</span>
                {v}
              </button>
            ))}
          </div>
        </div>
      </header>
      <main className="workspace"
        style={{ "--cols": shown.map((v) => `minmax(0, ${sizes[v]}fr)`).join(" 6px ") } as CSSProperties}>
        {shown.map((view, i) => (
          <Fragment key={view}>
            {i > 0 && <Splitter label={`Resize ${shown[i - 1]} and ${view}`} onStart={() => startResize(shown[i - 1], view)} />}
            {views[view]}
          </Fragment>
        ))}
      </main>
    </div>
  );
}
