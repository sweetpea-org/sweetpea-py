import type { Row } from "../api";
import type { Check, Model } from "../model";
import BlockBox, { type Selection } from "./BlockBox";
import Timeline from "./Timeline";

type Props = Selection & { model: Model; check: Check; sample: Row[] | null; onChange: (model: Model) => void };

export default function BlocksPanel({ model, check, sample, onChange, selected, onSelect }: Props) {
  return (
    <div className="blocks-panel">
      <p className="intro">
        A <strong>block</strong> crosses factors so every combination of their levels appears. Use{" "}
        <em>Arrange…</em> to nest a block inside another, run blocks at the same time (merge), or repeat one.
      </p>
      <Timeline block={model.block} nodes={check.nodes} sample={sample} />
      <BlockBox model={model} check={check} onChange={onChange} block={model.block}
        selected={selected} onSelect={onSelect} />
    </div>
  );
}
