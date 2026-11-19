import type { KeyboardEvent, PointerEvent } from "react";

type Props = {
  /** Called when a drag starts; returns what to do as the handle moves ``dx`` pixels from where it started. */
  onStart: () => (dx: number) => void;
  label: string;
};

// How far one arrow-key press moves the handle.
const KEY_STEP = 24;

/** A draggable handle between two panes: dragging it widens one and narrows the other. */
export default function Splitter({ onStart, label }: Props) {
  function start(e: PointerEvent<HTMLDivElement>) {
    const handle = e.currentTarget;
    const x0 = e.clientX;
    const resize = onStart();
    handle.setPointerCapture(e.pointerId);
    const move = (ev: globalThis.PointerEvent) => resize(ev.clientX - x0);
    const stop = () => {
      handle.removeEventListener("pointermove", move);
      handle.removeEventListener("pointerup", stop);
    };
    handle.addEventListener("pointermove", move);
    handle.addEventListener("pointerup", stop);
  }

  function key(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === "ArrowLeft") onStart()(-KEY_STEP);
    if (e.key === "ArrowRight") onStart()(KEY_STEP);
  }

  return (
    <div className="splitter" role="separator" aria-orientation="vertical" aria-label={label} tabIndex={0}
      title={label} onPointerDown={start} onKeyDown={key} />
  );
}

/** Hides a view; disabled when ``onHide`` is missing because the view is the only one left. */
export function HideButton({ onHide, label }: { onHide?: () => void; label: string }) {
  return (
    <button className="small" disabled={!onHide} onClick={onHide}
      title={onHide ? `Hide ${label} (show it again from the top bar)` : "The last visible view can't be hidden"}>
      Hide
    </button>
  );
}
