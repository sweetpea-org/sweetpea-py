import { useEffect, useState } from "react";

type Props = {
  value: string;
  onCommit: (value: string) => void;
  /** Rejects a value by returning why; the input then reverts. */
  validate?: (value: string) => string | null;
  placeholder?: string;
  className?: string;
};

/** A text input that applies its value on Enter or blur, so that renames
 * are not applied one keystroke at a time. */
export default function CommitInput({ value, onCommit, validate, placeholder, className }: Props) {
  const [draft, setDraft] = useState(value);
  const [problem, setProblem] = useState<string | null>(null);
  useEffect(() => setDraft(value), [value]);

  function commit() {
    const text = draft.trim();
    const why = text === "" ? "A name is required" : validate?.(text) ?? null;
    setProblem(why);
    if (why) setDraft(value);
    else if (text !== value) onCommit(text);
  }

  return (
    <input
      className={problem ? `${className ?? ""} invalid` : className}
      value={draft}
      placeholder={placeholder}
      title={problem ?? undefined}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
    />
  );
}
