import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { VerdictBanner, VerdictState } from "./VerdictBanner";
import { useAutoResize } from "./Stepper";
import { onRender } from "./streamlit";

type Args = {
  state: VerdictState;
  headline: string;
  subtitle?: string;
};

function App() {
  const [args, setArgs] = useState<Args | null>(null);
  const ref = useAutoResize([args]);

  useEffect(() => {
    onRender<Args>((p) => setArgs(p.args));
  }, []);

  if (!args) return <div ref={ref} />;
  return (
    <div ref={ref} className="px-1 py-2">
      <VerdictBanner
        state={args.state}
        headline={args.headline}
        subtitle={args.subtitle}
      />
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
