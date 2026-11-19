import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { parseCondition, refText, ruleText } from "../conditions";
import { findFactor, lagOf, type Factor, type Model, type Rule } from "../model";

type Props = { rule: Rule; factor: Factor; model: Model; onChange: (rule: Rule) => void };
type Suggestion = { insert: string; label: string; help: string };

// The most suggestions shown at once.
const MAX_SUGGESTIONS = 8;

// Python words a condition may use.
const WORDS: Suggestion[] = [
  { insert: "and", label: "and", help: "both hold" },
  { insert: "or", label: "or", help: "either holds" },
  { insert: "not", label: "not", help: "doesn't hold" },
  { insert: "in", label: "in", help: "is one of, such as in (\"a\", \"b\")" },
  { insert: "True", label: "True", help: "always" },
  { insert: "False", label: "False", help: "never" },
];

/** A condition typed as a Python expression, applied on Enter or when the box loses focus.
 * Text that can't be read keeps the previous condition and says why. */
export default function ConditionInput({ rule, factor, model, onChange }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [draft, setDraft] = useState(ruleText(rule, factor));
  const [error, setError] = useState<string | null>(null);
  const [focused, setFocused] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [active, setActive] = useState(0);
  const text = ruleText(rule, factor);
  useEffect(() => setDraft(text), [text]);

  const lag = lagOf(factor);
  const inputs = factor.inputs ?? [];
  const trials = lag ? [0, -lag] : [0];
  const trialHelp = (at: number) => (!lag ? "factor" : at === 0 ? "this trial" : lag === 1 ? "previous trial" : `${lag} trials back`);
  const candidates: Suggestion[] = [
    ...inputs.flatMap((n) => trials.map((at) => {
      const ref = refText(factor, n, at);
      return { insert: ref, label: ref, help: trialHelp(at) };
    })),
    ...inputs.flatMap((n) => (findFactor(model, n)?.levels ?? []).map((l) => ({
      insert: `"${l.name}"`, label: `"${l.name}"`, help: `level of ${n}`,
    }))),
    ...WORDS,
  ];
  const [a, b] = [inputs[0], inputs[1] ?? inputs[0]];
  const level = findFactor(model, a)?.levels[0]?.name ?? "x";
  const examples = a ? [
    lag ? `${refText(factor, a, 0)} == ${refText(factor, a, -lag)}` : `${refText(factor, a, 0)} == ${refText(factor, b, 0)}`,
    `${refText(factor, a, 0)} != "${level}"`,
    `${refText(factor, a, -lag)} in ("${level}", …)`,
  ] : [];

  // The word being typed: the run of name characters or an open quote just before the cursor.
  const typedWord = (text: string, cursor: number) => text.slice(0, cursor).match(/("[^"]*|[\w]+)$/)?.[0] ?? "";

  function suggest(text: string, cursor: number) {
    const word = typedWord(text, cursor).toLowerCase();
    const matches = word ? candidates.filter((c) => c.insert.toLowerCase().startsWith(word) && c.insert.toLowerCase() !== word) : [];
    setSuggestions(matches.slice(0, MAX_SUGGESTIONS));
    setActive(0);
  }

  function accept(s: Suggestion) {
    const el = input.current!;
    const cursor = el.selectionStart ?? draft.length;
    const start = cursor - typedWord(draft, cursor).length;
    const next = draft.slice(0, start) + s.insert + draft.slice(cursor);
    setDraft(next);
    setSuggestions([]);
    requestAnimationFrame(() => el.setSelectionRange(start + s.insert.length, start + s.insert.length));
  }

  function commit() {
    const parsed = parseCondition(draft, factor, model);
    if ("error" in parsed) {
      setError(parsed.error);
      return;
    }
    setError(null);
    if (ruleText(parsed.rule, factor) !== text) onChange(parsed.rule);
    else setDraft(text);
  }

  function key(e: KeyboardEvent<HTMLInputElement>) {
    if (suggestions.length && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
      e.preventDefault();
      setActive((active + (e.key === "ArrowDown" ? 1 : suggestions.length - 1)) % suggestions.length);
    } else if (suggestions.length && (e.key === "Enter" || e.key === "Tab")) {
      e.preventDefault();
      accept(suggestions[active]);
    } else if (e.key === "Escape") {
      setSuggestions([]);
    } else if (e.key === "Enter") {
      commit();
    }
  }

  return (
    <div className="condition">
      <input ref={input} className={error ? "condition-input invalid" : "condition-input"} value={draft} spellCheck={false}
        title="Type a Python condition; suggestions appear as you type. Press Enter to apply."
        onChange={(e) => {
          setDraft(e.target.value);
          suggest(e.target.value, e.target.selectionStart ?? e.target.value.length);
        }}
        onKeyDown={key}
        onFocus={() => setFocused(true)}
        onBlur={() => {
          setFocused(false);
          setSuggestions([]);
          commit();
        }} />
      {suggestions.length > 0 && (
        <ul className="suggestions" role="listbox">
          {suggestions.map((s, i) => (
            <li key={s.insert} role="option" aria-selected={i === active} className={i === active ? "active" : undefined}
              // Keeps focus in the box, so choosing a suggestion doesn't apply the half-typed text.
              onMouseDown={(e) => {
                e.preventDefault();
                accept(s);
              }}>
              <code>{s.label}</code> <span className="hint">{s.help}</span>
            </li>
          ))}
        </ul>
      )}
      {error && <p className="condition-error">{error}. The previous condition is kept.</p>}
      {focused && !error && (
        <p className="hint condition-help">
          Python, such as {examples.map((e, i) => <span key={i}>{i > 0 && " · "}<code>{e}</code></span>)} · combine
          with <code>and</code>, <code>or</code>, <code>not</code>
        </p>
      )}
    </div>
  );
}
