import { useRef, type ChangeEvent } from "react";

export type CodeError = { error: string; line: number | null };

type Props = { code: string; error: CodeError | null; onChange: (code: string) => void };

export function download(filename: string, text: string, type: string) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([text], { type }));
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

export default function CodePane({ code, error, onChange }: Props) {
  const gutter = useRef<HTMLDivElement>(null);
  const lines = code.split("\n").length;

  async function open(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) onChange(await file.text());
    event.target.value = "";
  }

  return (
    <aside className="code-pane">
      <div className="code-toolbar">
        <h2>Python</h2>
        <span className="hint">Edit here or in the designer — each updates the other.</span>
        <label className="button">
          Open .py
          <input type="file" accept=".py" hidden onChange={open} />
        </label>
        <button onClick={() => download("experiment.py", code, "text/x-python")}>Save .py</button>
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
