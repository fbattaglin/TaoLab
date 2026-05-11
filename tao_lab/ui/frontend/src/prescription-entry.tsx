import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { PrescriptionCard, PrescriptionCardProps } from "./PrescriptionCard";
import { useAutoResize } from "./Stepper";
import { onRender } from "./streamlit";

interface Args extends PrescriptionCardProps {
  theme_vars?: string;
}

function App() {
  const [args, setArgs] = useState<Args | null>(null);
  const ref = useAutoResize([args]);

  useEffect(() => {
    onRender<Args>((p) => {
      setArgs(p.args);
      if (p.args.theme_vars) {
        document.documentElement.style.cssText = p.args.theme_vars;
      } else {
        document.documentElement.style.cssText = "";
      }
    });
  }, []);

  if (!args) return <div ref={ref} />;
  return (
    <div ref={ref} className="px-1 py-2">
      <PrescriptionCard {...args} />
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
