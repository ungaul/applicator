import { useState, useRef } from "react";
import toast from "react-hot-toast";
import { generateDocs, fetchJobDetails } from "../../lib/api";
import { useJobStore } from "../../store/jobStore";

function FileDropzone({ label, file, onFile, accept }) {
  const inputRef = useRef();
  const [over, setOver] = useState(false);

  return (
    <div>
      <label>{label}</label>
      <div
        className={`dropzone ${over ? "over" : ""}`}
        onClick={() => inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          const f = e.dataTransfer.files[0];
          if (f) onFile(f);
        }}
      >
        {file
          ? <span className="filename">📄 {file.name}</span>
          : <span>Glisse ou clique pour choisir<br /><small style={{ color: "var(--muted)" }}>{accept}</small></span>
        }
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          style={{ display: "none" }}
          onChange={(e) => e.target.files[0] && onFile(e.target.files[0])}
        />
      </div>
    </div>
  );
}

export default function DocPanel({ onClose }) {
  const getToGenerate = useJobStore((s) => s.getToGenerate);
  const updateJob     = useJobStore((s) => s.updateJob);
  const addTokens     = useJobStore((s) => s.addTokens);

  const toGenerate = getToGenerate();

  const [cvFile,  setCvFile]  = useState(null);
  const [lmFile,  setLmFile]  = useState(null);
  const [loading, setLoading] = useState(false);

  const canGenerate = cvFile && lmFile && toGenerate.length > 0;

  const handleGenerate = async () => {
    if (!cvFile || !lmFile) { toast.error("Ajoute les deux templates (CV + LM)"); return; }
    if (toGenerate.length === 0) {
      toast.error("Aucune offre avec le statut « à générer » sélectionnée");
      return;
    }

    setLoading(true);

    try {
      const jobs = await Promise.all(
        toGenerate.map(async (job) => {
          if (!job.description && job.url && job.source) {
            try {
              const details = await fetchJobDetails(job.url, job.source);
              updateJob(job.id, details);
              return { ...job, ...details };
            } catch {}
          }
          return job;
        })
      );

      const tokens = await generateDocs({ cvFile, lmFile, jobs });

      toGenerate.forEach((job) => updateJob(job.id, { status: "à postuler" }));
      if (tokens) addTokens(tokens);

      toast.success(`${toGenerate.length} candidature(s) générée(s) !`);
      onClose();
    } catch (err) {
      toast.error(`Erreur : ${err.response?.data?.detail ?? err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="panel-header">
        <h2>générer les docs</h2>
        <button className="btn-icon" onClick={onClose}>✕</button>
      </div>

      <div className="panel-body">
        <div style={{ padding: "10px", background: "var(--bg3)", borderRadius: "var(--radius)", fontSize: 12, color: "var(--muted)", lineHeight: 1.7 }}>
          {toGenerate.length === 0
            ? <>Aucune offre <span style={{ color: "#a855f7" }}>à générer</span> sélectionnée.<br />Coche des offres avec ce statut.</>
            : <><strong style={{ color: "#a855f7" }}>{toGenerate.length}</strong> offre(s) à traiter :<br />{toGenerate.map(j => j.company).join(", ")}</>
          }
        </div>

        <FileDropzone label="Template CV"                    file={cvFile} onFile={setCvFile} accept=".docx,.doc" />
        <FileDropzone label="Template Lettre de motivation"  file={lmFile} onFile={setLmFile} accept=".docx,.doc" />

        <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.7 }}>
          Un zip sera téléchargé avec un sous-dossier par entreprise.<br />
          Chaque dossier contient : CV, LM, et un email prêt à envoyer (.eml).
        </div>

        <button
          className="btn btn-primary"
          onClick={handleGenerate}
          disabled={loading || !canGenerate}
        >
          {loading
            ? <><span className="spinner" />&nbsp;génération en cours…</>
            : `générer (${toGenerate.length} offre${toGenerate.length > 1 ? "s" : ""})`
          }
        </button>
      </div>
    </>
  );
}