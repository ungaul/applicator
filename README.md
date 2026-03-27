# applicator

> This project if a WIP. Please check the results and send an issue ticket if you have any issue/feature request.

## Stack

- **Backend** — Python / FastAPI
- **Frontend** — React / Vite
- **AI** — OpenRouter (configurable model)

## Features

- Search jobs across France Travail, HelloWork, LinkedIn, Welcome to the Jungle, Adzuna
- Spreadsheet-style job board with editable fields and status tracking (à générer → à postuler → postulé → relancé → rejeté → accepté)
- AI-powered document generation: adapts CV headline + cover letter + email per job
- Outputs a zip per company with `CV Firstname Lastname.docx`, `LM Firstname Lastname.docx`, and `email.eml` with attachments
- All data persisted in localStorage

## API
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/jobs/search` | Search jobs across sources |
| `POST` | `/jobs/fetch` | Scrape full job description from URL |
| `POST` | `/docs/generate` | Generate adapted CV, LM and email |
| `GET` | `/health` | Health check |

## Setup

Download [docker-compose-example.yml](docker-compose-example.yml), then in a terminal from its folder:
```bash
docker compose up -d
```

- Frontend → http://localhost:3001
- Backend → http://localhost:8001

Do NOT expose it to the public Internet, as your OpenRouter API key can be used by every user of the app. 

## Credit

I adapted the work of [Zeffut](https://github.com/Zeffut/JobScraper) for job listings' scraping.