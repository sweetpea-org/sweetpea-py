import { defaultRule, findFactor, isRef, type Kind, type Model, type Rule, type Term } from "../model";

type Props = {
  rule: Rule;
  model: Model;
  inputs: string[];
  kind: Kind;
  onChange: (rule: Rule) => void;
};

type GroupMode = "all" | "any" | "none" | "notall";
const GROUP_LABELS: Record<GroupMode, string> = {
  all: "All of these are true",
  any: "Any of these is true",
  none: "None of these is true",
  notall: "Not all of these are true",
};

function termLabel(term: Term, kind: Kind): string {
  if (!isRef(term)) return `“${term.level}”`;
  if (kind === "within") return term.factor;
  return `${term.factor} (${term.at === 0 ? "this trial" : "previous trial"})`;
}

function TermSelect({ term, options, kind, onChange }: {
  term: Term;
  options: Term[];
  kind: Kind;
  onChange: (t: Term) => void;
}) {
  const key = JSON.stringify(term);
  const all = options.some((o) => JSON.stringify(o) === key) ? options : [term, ...options];
  return (
    <select value={key} onChange={(e) => onChange(JSON.parse(e.target.value))}>
      {all.map((o) => (
        <option key={JSON.stringify(o)} value={JSON.stringify(o)}>
          {termLabel(o, kind)}
        </option>
      ))}
    </select>
  );
}

function Comparison({ rule, model, inputs, kind, onChange }: Props & { rule: Extract<Rule, { cmp: string }> }) {
  const positions = kind === "transition" ? [0, -1] : [0];
  const refs: Term[] = inputs.flatMap((factor) => positions.map((at) => ({ factor, at })));
  const left = rule.left;
  const levels: Term[] = isRef(left) ? (findFactor(model, left.factor)?.levels ?? []).map((l) => ({ level: l.name })) : [];

  function setLeft(term: Term) {
    // A level picked for the old factor means nothing for the new one.
    const right = isRef(rule.right) || !isRef(term)
      ? rule.right : { level: findFactor(model, term.factor)?.levels[0]?.name ?? "" };
    onChange({ ...rule, left: term, right });
  }

  return (
    <div className="comparison">
      <TermSelect term={left} options={refs} kind={kind} onChange={setLeft} />
      <select value={rule.cmp} onChange={(e) => onChange({ ...rule, cmp: e.target.value as "==" | "!=" })}>
        <option value="==">is</option>
        <option value="!=">is not</option>
      </select>
      <TermSelect term={rule.right} options={[...levels, ...refs.filter((r) => JSON.stringify(r) !== JSON.stringify(left))]}
        kind={kind} onChange={(right) => onChange({ ...rule, right })} />
    </div>
  );
}

function groupOf(rule: Rule): { mode: GroupMode; members: Rule[] } | null {
  if ("all" in rule) return { mode: "all", members: rule.all };
  if ("any" in rule) return { mode: "any", members: rule.any };
  if ("not" in rule && "any" in rule.not) return { mode: "none", members: rule.not.any };
  if ("not" in rule && "all" in rule.not) return { mode: "notall", members: rule.not.all };
  return null;
}

function makeGroup(mode: GroupMode, members: Rule[]): Rule {
  const group = mode === "all" || mode === "notall" ? { all: members } : { any: members };
  return mode === "none" || mode === "notall" ? { not: group } : group;
}

export default function RuleEditor(props: Props) {
  const { rule, model, inputs, onChange } = props;
  const group = groupOf(rule);

  if ("cmp" in rule) {
    return (
      <div className="rule">
        <Comparison {...props} rule={rule} />
        <button className="small" title="Combine with another condition"
          onClick={() => onChange({ all: [rule, defaultRule(model, inputs)] })}>
          + and / or
        </button>
      </div>
    );
  }

  if (!group) {
    // A negation of something other than a group.
    const inner = (rule as { not: Rule }).not;
    return (
      <div className="rule group">
        <span className="group-label">It is not the case that</span>
        <RuleEditor {...props} rule={inner} onChange={(r) => onChange({ not: r })} />
      </div>
    );
  }

  const setMember = (i: number, r: Rule) => onChange(makeGroup(group.mode, group.members.map((m, j) => (j === i ? r : m))));
  const removeMember = (i: number) => {
    const rest = group.members.filter((_, j) => j !== i);
    onChange(rest.length === 1 && group.mode === "all" ? rest[0] : makeGroup(group.mode, rest));
  };

  return (
    <div className="rule group">
      <select value={group.mode} onChange={(e) => onChange(makeGroup(e.target.value as GroupMode, group.members))}>
        {Object.entries(GROUP_LABELS).map(([mode, label]) => (
          <option key={mode} value={mode}>{label}</option>
        ))}
      </select>
      {group.members.map((member, i) => (
        <div className="member" key={i}>
          <RuleEditor {...props} rule={member} onChange={(r) => setMember(i, r)} />
          <button className="small remove" title="Remove condition" onClick={() => removeMember(i)}>×</button>
        </div>
      ))}
      <button className="small" onClick={() => onChange(makeGroup(group.mode, [...group.members, defaultRule(model, inputs)]))}>
        + condition
      </button>
    </div>
  );
}
