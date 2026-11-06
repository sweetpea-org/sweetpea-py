import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { api, type Example } from "../api";

export function download(filename: string, text: string, type: string) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([text], { type }));
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

type Props = { code: string; onOpen: (code: string) => void };

/** Import an example or a .py file (either replaces the current design), and save the program. */
export default function FileMenu({ code, onOpen }: Props) {
  const [examples, setExamples] = useState<Example[]>([]);
  const file = useRef<HTMLInputElement>(null);
  useEffect(() => {
    api.examples().then(setExamples);
  }, []);

  function choose(value: string) {
    if (value === "file") file.current!.click();
    else onOpen(examples[Number(value)].code);
  }

  async function openFile(event: ChangeEvent<HTMLInputElement>) {
    const chosen = event.target.files?.[0];
    if (chosen) onOpen(await chosen.text());
    event.target.value = "";
  }

  return (
    <div className="file-menu">
      <select className="import-menu" value="" title="Replace the current design with an example or your own .py file"
        onChange={(e) => choose(e.target.value)}>
        <option value="">Import…</option>
        <optgroup label="Examples">
          {examples.map((ex, i) => <option key={ex.title} value={i} title={ex.description}>{ex.title}</option>)}
        </optgroup>
        <optgroup label="Your own">
          <option value="file">A .py file…</option>
        </optgroup>
      </select>
      <input ref={file} type="file" accept=".py" hidden onChange={openFile} />
      <button title="Download the program as a .py file" onClick={() => download("experiment.py", code, "text/x-python")}>
        Save .py
      </button>
    </div>
  );
}
