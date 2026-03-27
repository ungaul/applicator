import axios from "axios";

const api = axios.create({
  baseURL: typeof __API_URL__ !== "undefined" ? __API_URL__ : "http://localhost:8001",
  timeout: 120000,
});

export async function searchJobs(params) {
  const { data } = await api.post("/jobs/search", params);
  return data.jobs;
}

export async function fetchJobDetails(url, source) {
  const { data } = await api.post("/jobs/fetch", { url, source });
  return data;
}

export async function generateDocs({ cvFile, lmFile, jobs }) {
  const form = new FormData();
  form.append("cv_template", cvFile);
  form.append("lm_template", lmFile);
  form.append("jobs_json", JSON.stringify(jobs.map((j) => ({
    title:       j.title       ?? "Poste",
    company:     j.company     ?? "Entreprise",
    description: j.description ?? "",
    url:         j.url         ?? "",
  }))));

  const resp = await api.post("/docs/generate", form, {
    responseType: "blob",
  });

  const tokens = parseInt(resp.headers["x-total-tokens"] ?? "0", 10);

  const disposition = resp.headers["content-disposition"] ?? "";
  const match = disposition.match(/filename="?([^";\n]+)"?/);
  const filename = match?.[1] ?? "candidatures.zip";

  const url = URL.createObjectURL(resp.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);

  return tokens;
}