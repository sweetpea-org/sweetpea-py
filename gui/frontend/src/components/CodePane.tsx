import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { api, type Example } from "../api";
import { HideButton } from "./Splitter";

export type CodeError = { error: string; line: number | null };

type Props = { code: string; error: CodeError | null; onChange: (code: string) => void; onHide?: () => void };

export function download(filename: string, text: string, type: string) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([text], { type }));
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

export default function CodePane({ code, error, onChange, onHide }: Props) {
  const gutter = useRef<HTMLDivElement>(null);
  const [examples, setExamples] = useState<Example[]>([]);
  useEffect(() => {
    api.examples().then(setExamples);
  }, []);
  const lines = code.split("\n").length;

  async function open(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) onChange(await file.text());
    event.target.value = "";
  }

  return (
    <aside className="code-pane" data-view="Code">
      <div className="code-toolbar">
        <h2>Python</h2>
        <span className="hint">Edit here or in the designer — each updates the other.</span>
        <label className="button">
          Open .py
          <input type="file" accept=".py" hidden onChange={open} />
        </label>
        <button onClick={() => download("experiment.py", code, "text/x-python")}>Save .py</button>
        {/* An example opens like a file: its code replaces the current design. */}
        <select className="examples" value="" title="Open an example design, replacing the current one"
          onChange={(e) => onChange(examples[Number(e.target.value)].code)}>
          <option value="">Examples…</option>
          {examples.map((ex, i) => <option key={ex.title} value={i} title={ex.description}>{ex.title}</option>)}
        </select>
        <HideButton onHide={onHide} label="the code" />
      </div>
      <div className="code-editor">
        <div className="gutter" ref={gutter} aria-hidden>
          {Array.from({ length: lines }, (_, i) => (
            <div key={i} className={error?.line === i + 1 ? "bad-line" : undefined}>
              {i + 1}
            </div>
          ))}
        </div>
        <textarea
          value={code}
          spellCheck={false}
          aria-label="SweetPea program"
          onChange={(e) => onChange(e.target.value)}
          onScroll={(e) => gutter.current && (gutter.current.scrollTop = e.currentTarget.scrollTop)}
        />
      </div>
    </aside>
  );
}
