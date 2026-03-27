import { useState } from "react";
import { Toaster } from "react-hot-toast";
import JobBoard from "./components/board/JobBoard";
import SearchPanel from "./components/search/SearchPanel";
import DocPanel from "./components/docs/DocPanel";
import { useJobStore } from "./store/jobStore";
import "./index.css";

export default function App() {
  const [panel, setPanel] = useState(null);
  const { totalTokens, resetTokens } = useJobStore();

  return (
    <div className="app">
      <Toaster position="bottom-right" toastOptions={{ duration: 3500 }} />

      <header className="topbar">
        <span className="logo">app<em>licator</em></span>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontFamily: "var(--mono)", color: "var(--muted)" }}>
          <span title="Tokens IA consommés depuis le démarrage">
            ⬡ {totalTokens.toLocaleString()} tokens
          </span>
          {totalTokens > 0 && (
            <button className="btn-icon" style={{ fontSize: 11 }} onClick={resetTokens} title="Remettre à zéro">✕</button>
          )}
        </div>
        <nav>
          <button
            className={`nav-btn ${panel === "search" ? "active" : ""}`}
            onClick={() => setPanel(panel === "search" ? null : "search")}
          >
            + chercher des offres
          </button>
          <button
            className={`nav-btn ${panel === "docs" ? "active" : ""}`}
            onClick={() => setPanel(panel === "docs" ? null : "docs")}
          >
            générer les docs
          </button>
        </nav>
      </header>

      <main className="main">
        {panel === "search" && (
          <aside className="side-panel">
            <SearchPanel onClose={() => setPanel(null)} />
          </aside>
        )}
        {panel === "docs" && (
          <aside className="side-panel">
            <DocPanel onClose={() => setPanel(null)} />
          </aside>
        )}
        <section className="board-wrap">
          <JobBoard />
        </section>
      </main>
    </div>
  );
}
