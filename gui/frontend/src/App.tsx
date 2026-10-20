import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { STARTER, type Check, type Model } from "./model";
import CodePane, { type CodeError } from "./components/CodePane";
import ConstraintsPanel from "./components/ConstraintsPanel";
import DesignPanel from "./components/DesignPanel";
import FactorsPanel from "./components/FactorsPanel";
import GeneratePanel from "./components/GeneratePanel";

const STEPS = ["Factors", "Design", "Constraints", "Generate"] as const;
type Step = (typeof STEPS)[number];

// How long typing in the code pane pauses before the GUI catches up.
const PARSE_DELAY_MS = 400;

export default function App() {
  const [model, setModel] = useState<Model>(STARTER);
  const [code, setCode] = useState("");
  const [check, setCheck] = useState<Check>({});
  const [codeError, setCodeError] = useState<CodeError | null>(null);
  const [step, setStep] = useState<Step>("Factors");
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
      setCheck(parsed.check);
      setCodeError(null);
    }
  }

  function editModel(next: Model) {
    window.clearTimeout(parseTimer.current);
    setModel(next);
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
    Design: <DesignPanel model={model} check={check} onChange={editModel} />,
    Constraints: <ConstraintsPanel model={model} onChange={editModel} />,
    Generate: <GeneratePanel model={model} check={check} onChange={editModel} />,
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
        <div className={check.error ? "status error" : "status"}>
          {check.error ? "Design has a problem" : check.trials !== undefined ? `${check.trials} trials per sequence` : ""}
        </div>
      </header>
      <main className="workspace">
        <section className="panel">
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
        <CodePane code={code} error={codeError} onChange={editCode} />
      </main>
    </div>
  );
}
