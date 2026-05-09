import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { Stepper, StepDescriptor, useAutoResize } from "./Stepper";
import { onRender } from "./streamlit";

type Args = {
  steps: StepDescriptor[];
  clickable?: boolean;
};

function App() {
  const [args, setArgs] = useState<Args | null>(null);
  const ref = useAutoResize([args]);

  useEffect(() => {
    onRender<Args>((payload) => setArgs(payload.args));
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
