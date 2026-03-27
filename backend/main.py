from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.jobs import router as jobs_router
from routes.docs import router as docs_router

app = FastAPI(title="Applicator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Total-Tokens"],
    expose_headers=["X-Total-Tokens", "Content-Disposition"],
)

app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(docs_router, prefix="/docs", tags=["docs"])

@app.get("/health")
def health():
    return {"status": "ok"}
