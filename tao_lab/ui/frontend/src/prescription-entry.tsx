import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { PrescriptionCard, PrescriptionCardProps } from "./PrescriptionCard";
import { useAutoResize } from "./Stepper";
import { onRender } from "./streamlit";

function App() {
  const [args, setArgs] = useState<PrescriptionCardProps | null>(null);
  const ref = useAutoResize([args]);

  useEffect(() => {
    onRender<PrescriptionCardProps>((p) => setArgs(p.args));
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
