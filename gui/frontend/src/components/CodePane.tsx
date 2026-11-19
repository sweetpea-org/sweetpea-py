import { useEffect, useRef } from "react";
import { python } from "@codemirror/lang-python";
import { setDiagnostics, type Diagnostic } from "@codemirror/lint";
import { Annotation } from "@codemirror/state";
import { oneDark } from "@codemirror/theme-one-dark";
import { EditorView, basicSetup } from "codemirror";
import { HideButton } from "./Splitter";

export type CodeError = { error: string; line: number | null };

type Props = { code: string; error: CodeError | null; onChange: (code: string) => void; onHide?: () => void };

// Marks edits that come from the designer, which must not be reported back as typing.
const fromDesigner = Annotation.define<boolean>();

export default function CodePane({ code, error, onChange, onHide }: Props) {
  const host = useRef<HTMLDivElement>(null);
  const view = useRef<EditorView>();
  // The editor is built once, so it reads the latest callback through a ref.
  const report = useRef(onChange);
  report.current = onChange;

  useEffect(() => {
    view.current = new EditorView({
      parent: host.current!,
      doc: code,
      extensions: [
        basicSetup,
        python(),
        oneDark,
        EditorView.updateListener.of((update) => {
          if (update.docChanged && !update.transactions.some((t) => t.annotation(fromDesigner))) {
            report.current(update.state.doc.toString());
          }
        }),
      ],
    });
    return () => view.current?.destroy();
  }, []);

  useEffect(() => {
    const editor = view.current!;
    if (editor.state.doc.toString() !== code) {
      editor.dispatch({ changes: { from: 0, to: editor.state.doc.length, insert: code }, annotations: fromDesigner.of(true) });
    }
  }, [code]);

  // Underlines the line the designer could not read.
  useEffect(() => {
    const editor = view.current!;
    const doc = editor.state.doc;
    const diagnostics: Diagnostic[] = error?.line && error.line <= doc.lines
      ? [{ from: doc.line(error.line).from, to: doc.line(error.line).to, severity: "error", message: error.error }]
      : [];
    editor.dispatch(setDiagnostics(editor.state, diagnostics));
  }, [error, code]);

  return (
    <aside className="code-pane" data-view="Code">
      <div className="code-toolbar">
        <h2>Python</h2>
        <span className="hint">Edit here or in the designer — each updates the other.</span>
        <HideButton onHide={onHide} label="the code" />
      </div>
      <div className="code-editor" ref={host} aria-label="SweetPea program" />
    </aside>
  );
}
