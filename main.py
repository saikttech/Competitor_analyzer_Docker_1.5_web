import logging
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from celery.result import AsyncResult

from celery_app import celery_app
from tasks import analyze_competitors_task
from config import API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Competitor Analyzer API",
    version="1.5",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_api_key(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return True


class AnalysisRequest(BaseModel):
    niche: str
    geo: str
    query: str
    clear_db: bool = False


@app.post("/analyze", dependencies=[Depends(verify_api_key)])
async def start_analysis(req: AnalysisRequest):
    task = analyze_competitors_task.apply_async(
        args=[req.niche, req.geo, req.query, req.clear_db]
    )
    logger.info(f"Task {task.id} sent to queue")
    return {"task_id": task.id, "status": "PENDING"}


@app.get("/analyze/{task_id}", dependencies=[Depends(verify_api_key)])
async def get_analysis_status(task_id: str):
    task = AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": task.status,
        "meta": None,
        "result": None,
        "error": None
    }

    if task.status == "PENDING":
        response["meta"] = {"stage": "⏳ Ожидание в очереди..."}
    elif task.status == "STARTED":
        response["meta"] = task.info or {"stage": "⚙️ Обработка..."}
    elif task.status == "SUCCESS":
        response["result"] = task.result
    elif task.status == "FAILURE":
        response["error"] = str(task.result)

    return response


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.5"}