import os
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from services.doc_engine import generate_documents

router = APIRouter()

@router.post("/generate")
async def generate_docs(
    cv_template:     UploadFile = File(...),
    lm_template:     UploadFile = File(...),
    jobs_json:       str        = Form(...),
):
    if not cv_template.filename or not lm_template.filename:
        raise HTTPException(status_code=400, detail="Les deux fichiers templates sont requis")

    cv_ext = os.path.splitext(cv_template.filename)[1].lower()
    lm_ext = os.path.splitext(lm_template.filename)[1].lower()

    allowed = {".docx", ".doc"}
    if cv_ext not in allowed or lm_ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Formats acceptés : docx uniquement (pas de PDF). Reçu : {cv_ext}, {lm_ext}"
        )

    try:
        jobs = json.loads(jobs_json)
        if not isinstance(jobs, list) or len(jobs) == 0:
            raise HTTPException(status_code=400, detail="jobs_json doit être une liste non vide")
        for j in jobs:
            print(f"[route/docs] {j.get('company')} | location={repr(j.get('location'))}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="jobs_json invalide")

    try:
        cv_bytes = await cv_template.read()
        lm_bytes = await lm_template.read()

        result_path, total_tokens = await generate_documents(
            cv_bytes=cv_bytes,
            cv_ext=cv_ext,
            lm_bytes=lm_bytes,
            lm_ext=lm_ext,
            jobs=jobs,
        )

        zip_name = os.path.basename(result_path)
        return FileResponse(
            result_path,
            media_type="application/zip",
            filename=zip_name,
            headers={
                "X-Total-Tokens":    str(total_tokens),
                "Access-Control-Expose-Headers": "X-Total-Tokens, Content-Disposition",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))