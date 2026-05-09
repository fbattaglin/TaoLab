/**
 * The hero verdict banner of the Prescription step.
 *
 * One of three states (ship / hold / dont_ship), each with its own colour
 * family and Lucide icon. The banner carries a label, a one-line headline
 * (the natural-language summary of the primary metric), and an optional
 * subtitle (e.g. confidence label).
 */

import { CircleCheck, CircleSlash, Pause, type LucideIcon } from "lucide-react";

export type VerdictState = "ship" | "hold" | "dont_ship";

export type VerdictBannerProps = {
  state: VerdictState;
  headline: string;
  subtitle?: string;
};

type Style = {
  label: string;
  Icon: LucideIcon;
  /** Tailwind classes for the wrapping card. */
  wrap: string;
  /** Tailwind classes for the icon halo. */
  halo: string;
  /** Tailwind classes for the bold label text. */
  labelClass: string;
};

const STYLES: Record<VerdictState, Style> = {
  ship: {
    label: "Ship it.",
    Icon: CircleCheck,
    wrap: "bg-success/5 ring-1 ring-success/30",
    halo: "bg-success/15 text-success",
    labelClass: "text-success",
  },
  hold: {
    label: "Hold.",
    Icon: Pause,
    wrap: "bg-warning/5 ring-1 ring-warning/30",
    halo: "bg-warning/15 text-warning",
    labelClass: "text-warning",
  },
  dont_ship: {
    label: "Don't ship.",
    Icon: CircleSlash,
    wrap: "bg-danger/5 ring-1 ring-danger/30",
    halo: "bg-danger/15 text-danger",
    labelClass: "text-danger",
  },
};

export function VerdictBanner({ state, headline, subtitle }: VerdictBannerProps) {
  const s = STYLES[state];
  const { Icon } = s;
  return (
    <div className={`rounded-card ${s.wrap} p-6 font-sans flex items-start gap-5`}>
      <div
        className={`flex-none flex h-14 w-14 items-center justify-center rounded-full ${s.halo}`}
      >
        <Icon size={28} strokeWidth={2.25} />
      </div>
      <div className="min-w-0">
        <div className={`text-2xl font-semibold tracking-tightish ${s.labelClass}`}>
          {s.label}
        </div>
        <div className="mt-1.5 text-base leading-relaxed text-indigo-ink">
          {headline}
        </div>
        {subtitle && (
          <div className="mt-2 text-sm text-slate">{subtitle}</div>
        )}
      </div>
    </div>
  );
}
