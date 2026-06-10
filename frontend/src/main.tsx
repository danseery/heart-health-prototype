import React from "react";
import ReactDOM from "react-dom/client";
import { ShieldCheck } from "lucide-react";
import "./styles.css";

function App() {
  return (
    <main className="app-shell">
      <section className="intro">
        <div className="mark" aria-hidden="true">
          <ShieldCheck size={28} strokeWidth={2.2} />
        </div>
        <p className="eyebrow">Local prototype</p>
        <h1>HeartHealth AI</h1>
        <p className="lede">
          A secure-by-default local scaffold for the assessment, results,
          content, and AI coach workflows.
        </p>
        <div className="status-grid" aria-label="Prototype status">
          <div>
            <span>Frontend</span>
            <strong>React + Vite</strong>
          </div>
          <div>
            <span>Backend</span>
            <strong>FastAPI</strong>
          </div>
          <div>
            <span>Data</span>
            <strong>SQLite planned</strong>
          </div>
        </div>
        <p className="disclaimer">
          Educational prototype only. Do not enter real patient or personal
          health data.
        </p>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
