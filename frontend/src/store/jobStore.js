import { create } from "zustand";
import { persist } from "zustand/middleware";

export const JOB_STATUSES = ["à générer", "à postuler", "postulé", "relancé", "rejeté", "accepté"];

const STATUS_COLORS = {
  "à générer":  "#a855f7",
  "à postuler": "#6366f1",
  "postulé":    "#f59e0b",
  "relancé":    "#3b82f6",
  "rejeté":     "#ef4444",
  "accepté":    "#22c55e",
};

export const getStatusColor = (status) => STATUS_COLORS[status] ?? "#888";

const DEFAULT_JOB = {
  id: null,
  source: null,
  url: null,
  title: "",
  company: "",
  location: "",
  contract_type: null,
  salary: null,
  remote: null,
  posted_at: null,
  description: null,
  status: "à générer",
  applied_at: null,
  notes: "",
  selected: false,
};

function makeId() {
  return `local_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

export const useJobStore = create(
  persist(
    (set, get) => ({
      jobs: [],

      addJobs: (newJobs) =>
        set((state) => {
          const existingUrls = new Set(state.jobs.map((j) => j.url));
          const now = new Date().toISOString();
          const toAdd = newJobs
            .filter((j) => !existingUrls.has(j.url))
            .map((j) => ({ ...DEFAULT_JOB, ...j, id: j.id ?? makeId(), processed_at: now }));
          return { jobs: [...state.jobs, ...toAdd] };
        }),

      addManualJob: () =>
        set((state) => ({
          jobs: [
            { ...DEFAULT_JOB, id: makeId(), title: "Nouveau poste", added_manually: true },
            ...state.jobs,
          ],
        })),

      updateJob: (id, patch) =>
        set((state) => ({
          jobs: state.jobs.map((j) => (j.id === id ? { ...j, ...patch } : j)),
        })),

      deleteJob: (id) =>
        set((state) => ({ jobs: state.jobs.filter((j) => j.id !== id) })),

      deleteSelected: () =>
        set((state) => ({ jobs: state.jobs.filter((j) => !j.selected) })),

      toggleSelect: (id) =>
        set((state) => ({
          jobs: state.jobs.map((j) => (j.id === id ? { ...j, selected: !j.selected } : j)),
        })),

      selectAll: (val) =>
        set((state) => ({ jobs: state.jobs.map((j) => ({ ...j, selected: val })) })),

      getSelected: () => get().jobs.filter((j) => j.selected),

      markApplied: (id) =>
        set((state) => ({
          jobs: state.jobs.map((j) =>
            j.id === id ? { ...j, status: "postulé", applied_at: new Date().toISOString() } : j
          ),
        })),

      totalTokens: 0,
      addTokens: (n) => set((state) => ({ totalTokens: state.totalTokens + n })),
      resetTokens: () => set({ totalTokens: 0 }),

      getToGenerate: () => get().jobs.filter((j) => j.selected && j.status === "à générer"),
    }),
    {
      name: "applicator-board",
      version: 2,
    }
  )
);