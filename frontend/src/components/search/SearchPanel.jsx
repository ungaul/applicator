import { useState } from "react";
import toast from "react-hot-toast";
import { searchJobs } from "../../lib/api";
import { useJobStore } from "../../store/jobStore";

const SOURCES = ["francetravail", "hellowork", "linkedin", "wttj", "adzuna"];
const CONTRACTS = ["cdi", "cdd", "stage", "alternance", "freelance", "interim"];
const WORKPLACES = ["on_site", "remote", "hybrid"];
const EXPERIENCE = ["internship", "junior", "mid", "senior", "lead"];

function TagToggle({ options, value, onChange, labels = {} }) {
  return (
    <div className="tag-list">
      {options.map((o) => (
        <span
          key={o}
          className={`tag ${value.includes(o) ? "active" : ""}`}
          onClick={() =>
            onChange(value.includes(o) ? value.filter((v) => v !== o) : [...value, o])
          }
        >
          {labels[o] ?? o}
        </span>
      ))}
    </div>
  );
}

export default function SearchPanel({ onClose }) {
  const addJobs = useJobStore((s) => s.addJobs);

  const [keywords,   setKeywords]   = useState("");
  const [location,   setLocation]   = useState("France");
  const [radius,     setRadius]     = useState("");
  const [sources,    setSources]    = useState([]);
  const [contracts,  setContracts]  = useState([]);
  const [workplaces, setWorkplaces] = useState([]);
  const [experience, setExperience] = useState([]);
  const [maxResults, setMaxResults] = useState(10);
  const [loading,    setLoading]    = useState(false);

  const handleSearch = async () => {
    const kw = keywords.trim().split(/\s+/).filter(Boolean);
    if (!kw.length) { toast.error("Saisis au moins un mot-clé"); return; }

    setLoading(true);
    try {
      const jobs = await searchJobs({
        keywords: kw,
        location,
        radius_km: radius ? parseInt(radius) : null,
        sources,
        contract_types: contracts,
        workplace_types: workplaces,
        experience_levels: experience,
        max_results: maxResults,
      });
      addJobs(jobs);
      toast.success(`${jobs.length} offre(s) trouvée(s)`);
      onClose();
    } catch (err) {
      toast.error("Erreur : " + (err.response?.data?.detail ?? err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="panel-header">
        <h2>chercher des offres</h2>
        <button className="btn-icon" onClick={onClose}>✕</button>
      </div>
      <div className="panel-body">
        <div>
          <label>Mots-clés</label>
          <input type="text" value={keywords} onChange={(e) => setKeywords(e.target.value)}
            placeholder="ex. développeur react paris" onKeyDown={(e) => e.key === "Enter" && handleSearch()} />
        </div>
        <div>
          <label>Localisation</label>
          <input type="text" value={location} onChange={(e) => setLocation(e.target.value)} />
        </div>
        <div>
          <label>Rayon (km)</label>
          <input type="number" value={radius} onChange={(e) => setRadius(e.target.value)} placeholder="optionnel" min={0} />
        </div>
        <div>
          <label>Sources (toutes si vide)</label>
          <TagToggle options={SOURCES} value={sources} onChange={setSources} />
        </div>
        <div>
          <label>Type de contrat</label>
          <TagToggle options={CONTRACTS} value={contracts} onChange={setContracts} />
        </div>
        <div>
          <label>Mode de travail</label>
          <TagToggle options={WORKPLACES} value={workplaces} onChange={setWorkplaces}
            labels={{ on_site: "présentiel", remote: "remote", hybrid: "hybride" }} />
        </div>
        <div>
          <label>Expérience</label>
          <TagToggle options={EXPERIENCE} value={experience} onChange={setExperience} />
        </div>
        <div>
          <label>Max résultats par source</label>
          <input type="number" value={maxResults} onChange={(e) => setMaxResults(Number(e.target.value))} min={1} max={50} />
        </div>
        <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
          {loading ? <><span className="spinner" />&nbsp;recherche…</> : "lancer la recherche"}
        </button>
      </div>
    </>
  );
}
