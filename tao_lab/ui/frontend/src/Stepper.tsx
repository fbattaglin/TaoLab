import { Check } from "lucide-react";
import { useEffect, useRef } from "react";
import { setComponentValue, setFrameHeight } from "./streamlit";

export type StepStatus = "done" | "active" | "available" | "locked";

export type StepDescriptor = {
  index: number;
  label: string;
  status: StepStatus;
};

export type StepperProps = {
  steps: StepDescriptor[];
  /** When true, clicking a `done`/`available` step posts the index back to Python. */
  clickable?: boolean;
};

const RAIL = "h-px flex-1 bg-hairline";
const RAIL_DONE = "h-px flex-1 bg-tangerine/70";

/**
 * Horizontal 5-step stepper. One pill per step; rails between them tint
 * tangerine for completed segments. Active step gets a subtle ring + tangerine
 * dot; locked steps stay slate-soft. Click on a non-locked step posts that
 * step's index up so Python can navigate.
 */
export function Stepper({ steps, clickable = true }: StepperProps) {
  return (
    <nav className="w-full font-sans text-sm">
      <ol className="flex items-center gap-2">
        {steps.map((step, i) => {
          const reachable = step.status === "done" || step.status === "available";
          const isActive = step.status === "active";
          const isDone = step.status === "done";

          const onClick = () => {
            if (!clickable) return;
            if (!reachable) return;
            // Include a timestamp so Python can distinguish fresh clicks
            // from stale persisted values (Streamlit re-sends the last
            // setComponentValue on every rerun).
            setComponentValue({ step: step.index, ts: Date.now() });
          };

          return (
            <li key={step.index} className="flex flex-1 items-center gap-2">
              <button
                type="button"
                onClick={onClick}
                disabled={!clickable || (!reachable && !isActive)}
                aria-current={isActive ? "step" : undefined}
                className={[
                  "group flex flex-1 items-center gap-3 rounded-control px-3 py-2 transition",
                  "border",
                  isActive
                    ? "border-tangerine/30 bg-tangerine-soft text-indigo-deep"
                    : isDone
                      ? "border-hairline bg-cloud text-indigo-deep hover:border-slate-soft"
                      : reachable
                        ? "border-hairline bg-cloud text-slate hover:border-slate-soft"
                        : "border-hairline bg-cloud/60 text-slate-soft cursor-not-allowed",
                ].join(" ")}
              >
                <span
                  className={[
                    "flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold",
                    isActive
                      ? "bg-tangerine text-cloud"
                      : isDone
                        ? "bg-indigo-deep text-cloud"
                        : "bg-mist text-slate-soft border border-hairline",
                  ].join(" ")}
                >
                  {isDone ? <Check size={14} strokeWidth={3} /> : step.index}
                </span>
                <span className="truncate font-medium">{step.label}</span>
              </button>
              {i < steps.length - 1 && (
                <span
                  aria-hidden="true"
                  className={isDone ? RAIL_DONE : RAIL}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

/**
 * Auto-resizes the iframe to the rendered stepper's height after every render.
 */
export function useAutoResize(deps: unknown[] = []) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(() => {
      if (!ref.current) return;
      setFrameHeight(ref.current.getBoundingClientRect().height);
    });
    ro.observe(ref.current);
    setFrameHeight(ref.current.getBoundingClientRect().height);
    return () => ro.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return ref;
}
