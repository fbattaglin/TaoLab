/**
 * The hero deliverable. Designed to feel like a doctor's prescription pad:
 * a tangerine "PRESCRIPTION" eyebrow with a stamp affordance, structured
 * sections (Diagnosis / Confidence / Recommendation / Caveats / Next steps),
 * and tabular-num typography so values stay aligned in exports/screenshots.
 */

import {
  AlertTriangle,
  ArrowRight,
  CircleAlert,
  Info,
  type LucideIcon,
} from "lucide-react";

export type Severity = "info" | "warning" | "critical";

export type Caveat = {
  severity: Severity;
  title: string;
  body: string;
};

export type PrescriptionCardProps = {
  diagnosis: string;
  recommendation: string;
  reasoning: string;
  confidenceLabel: "strong" | "moderate" | "weak" | "none";
  confidenceScore: number; // 0..1
  caveats: Caveat[];
  nextSteps: string[];
};

const SEV_ICONS: Record<Severity, LucideIcon> = {
  info: Info,
  warning: AlertTriangle,
  critical: CircleAlert,
};

const SEV_COLORS: Record<Severity, string> = {
  info: "text-indigo-deep bg-mist border-hairline",
  warning: "text-warning bg-warning/5 border-warning/30",
  critical: "text-danger bg-danger/5 border-danger/30",
};

const CONF_LABEL: Record<PrescriptionCardProps["confidenceLabel"], string> = {
  strong: "Strong evidence",
  moderate: "Moderate evidence",
  weak: "Weak evidence",
  none: "No evidence",
};

export function PrescriptionCard(props: PrescriptionCardProps) {
  const {
    diagnosis,
    recommendation,
    reasoning,
    confidenceLabel,
    confidenceScore,
    caveats,
    nextSteps,
  } = props;

  return (
    <article
      className="font-sans bg-cloud border border-hairline rounded-card shadow-card overflow-hidden"
      aria-label="Prescription"
    >
      {/* ── Stamp eyebrow ── */}
      <div className="flex items-center justify-between px-7 pt-6">
        <div className="flex items-center gap-3">
          <div className="text-[0.7rem] uppercase tracking-[0.18em] text-tangerine font-bold">
            Prescription
          </div>
          <div className="h-px w-12 bg-tangerine/40" aria-hidden />
        </div>
        <div className="text-[0.7rem] uppercase tracking-[0.14em] text-slate-soft">
          tao lab
        </div>
      </div>

      <div className="px-7 pb-7 pt-3 space-y-6">
        {/* ── Diagnosis ── */}
        <Section label="Diagnosis">
          <p className="text-indigo-ink leading-relaxed">{diagnosis}</p>
        </Section>

        {/* ── Confidence ── */}
        <Section label="Confidence">
          <ConfidenceBar score={confidenceScore} label={CONF_LABEL[confidenceLabel]} />
        </Section>

        {/* ── Recommendation ── */}
        <Section label="Recommendation">
          <p className="text-indigo-ink leading-relaxed">{recommendation}</p>
        </Section>

        {/* ── Reasoning ── */}
        <Section label="Reasoning">
          <p className="text-slate leading-relaxed text-[0.95rem]">{reasoning}</p>
        </Section>

        {/* ── Caveats ── */}
        {caveats.length > 0 && (
          <Section label="Caveats">
            <ul className="space-y-2">
              {caveats.map((c, i) => {
                const Icon = SEV_ICONS[c.severity];
                return (
                  <li
                    key={i}
                    className={`flex gap-3 rounded-control border px-4 py-3 ${SEV_COLORS[c.severity]}`}
                  >
                    <Icon size={18} className="mt-0.5 flex-none" />
                    <div className="min-w-0">
                      <div className="font-semibold leading-snug">{c.title}</div>
                      <div className="mt-0.5 text-[0.92rem] leading-relaxed text-indigo-ink">
                        {c.body}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          </Section>
        )}

        {/* ── Next steps ── */}
        {nextSteps.length > 0 && (
          <Section label="Next steps">
            <ol className="space-y-2">
              {nextSteps.map((step, i) => (
                <li key={i} className="flex gap-3 text-indigo-ink leading-relaxed">
                  <ArrowRight
                    size={16}
                    className="mt-1 flex-none text-tangerine"
                  />
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </Section>
        )}
      </div>
    </article>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <section>
      <div className="text-[0.7rem] uppercase tracking-[0.12em] text-slate font-semibold mb-2">
        {label}
      </div>
      {children}
    </section>
  );
}

function ConfidenceBar({ score, label }: { score: number; label: string }) {
  const pct = Math.max(0, Math.min(1, score)) * 100;
  return (
    <div>
      <div className="h-2 rounded-full bg-mist overflow-hidden ring-1 ring-hairline">
        <div
          className="h-full bg-gradient-to-r from-tangerine to-indigo-deep transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-1.5 flex items-center justify-between text-[0.85rem]">
        <span className="text-indigo-deep font-medium">{label}</span>
        <span className="text-slate-soft tabular-nums">{Math.round(pct)} / 100</span>
      </div>
    </div>
  );
}
