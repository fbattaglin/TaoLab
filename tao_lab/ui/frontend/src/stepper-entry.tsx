import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { Stepper, StepDescriptor, useAutoResize } from "./Stepper";
import { onRender } from "./streamlit";

type Args = {
  steps: StepDescriptor[];
  clickable?: boolean;
  theme_vars?: string;
};

function App() {
  const [args, setArgs] = useState<Args | null>(null);
  const ref = useAutoResize([args]);

  useEffect(() => {
    onRender<Args>((payload) => {
      setArgs(payload.args);
      
      // Inject CSS variables from parent if provided (manual override)
      if (payload.args.theme_vars) {
        document.documentElement.style.cssText = payload.args.theme_vars;
      } else {
        // Clear any previous overrides for System mode
        document.documentElement.style.cssText = "";
      }
    });
  }, []);

  if (!args) return <div ref={ref} />;
  return (
    <div ref={ref} className="px-1 py-2">
      <Stepper steps={args.steps} clickable={args.clickable ?? true} />
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
