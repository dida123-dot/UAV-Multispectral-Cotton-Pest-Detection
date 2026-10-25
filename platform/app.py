"""线上仿真检测平台 —— FastAPI 入口。

启动方式（任选其一）：
    cd platform && uvicorn app:app --reload --port 8000
    uvicorn --app-dir platform app:app --port 8000

环境变量：
    YOLO_WEIGHTS      权重路径，默认 platform/weights/best.pt（缺失则进入 demo 模式）
    YOLO_CONF         置信度阈值，默认 0.25
    PLATFORM_DATA_DIR 数据目录，默认 platform/data
    MAX_UPLOAD_MB     单文件大小上限，默认 20
"""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

from inference import Detector, load_image
from severity import summarize, visible_vegetation_index
from storage import Store
from visualize import build_heatmap, draw_detections

BASE_DIR = Path(__file__).resolve().parent
WEIGHTS = Path(os.getenv("YOLO_WEIGHTS", str(BASE_DIR / "weights" / "best.pt")))
DATA_DIR = Path(os.getenv("PLATFORM_DATA_DIR", str(BASE_DIR / "data")))
RESULT_DIR = DATA_DIR / "results"
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024

RESULT_DIR.mkdir(parents=True, exist_ok=True)
detector = Detector(WEIGHTS, conf=float(os.getenv("YOLO_CONF", "0.25")))
store = Store(DATA_DIR / "tasks.db")


@asynccontextmanager
async def lifespan(_: FastAPI):
    detector.load()
    yield


app = FastAPI(title="新疆棉田病虫害智能识别平台", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _new_task_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]


def _read_upload(data: bytes) -> "object":
    if not data:
        raise HTTPException(status_code=400, detail="上传文件为空")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"文件超过 {MAX_UPLOAD_BYTES // 1024 // 1024} MB 限制")
    try:
        return load_image(data)
    except Exception as exc:  # noqa: BLE001 - 交由客户端看到具体原因
        raise HTTPException(status_code=400, detail=f"无法解析图像：{exc}") from exc


def _analyze(image, filename: str) -> dict:
    height, width = image.shape[:2]
    detections = [det.to_dict() for det in detector.predict(image)]
    veg_index = visible_vegetation_index(image)
    result = summarize(detections, (height, width), veg_index)

    task_id = _new_task_id()
    store.save(task_id, filename, detector.mode, (height, width), result)

    Image.fromarray(draw_detections(image, result["detections"])).save(RESULT_DIR / f"{task_id}.detected.png")
    Image.fromarray(build_heatmap((height, width), result["detections"])).save(RESULT_DIR / f"{task_id}.heatmap.png")

    result.update(
        {
            "task_id": task_id,
            "image": filename,
            "model": detector.mode,
            "size": {"width": width, "height": height},
            "urls": {
                "preview": f"/api/preview/{task_id}",
                "heatmap": f"/api/heatmap/{task_id}",
                "report": f"/api/report/{task_id}",
            },
        }
    )
    return result


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"mode": detector.mode, "tasks": store.list_tasks(10)},
    )


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": detector.mode,
        "classes": list(detector.class_names.values()),
        "weights": str(WEIGHTS),
    }


@app.post("/api/detect")
async def detect(file: UploadFile = File(...)) -> dict:
    image = _read_upload(await file.read())
    return _analyze(image, file.filename or "upload")


@app.post("/api/detect/batch")
async def detect_batch(files: list[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="未收到文件")
    results = [_analyze(_read_upload(await f.read()), f.filename or "upload") for f in files]
    return {"count": len(results), "results": results}


@app.get("/api/tasks")
def list_tasks(limit: int = 20) -> dict:
    return {"tasks": store.list_tasks(max(1, min(limit, 100)))}


@app.get("/api/report/{task_id}")
def report(task_id: str) -> dict:
    payload = store.get(task_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return payload


def _result_file(task_id: str, suffix: str) -> FileResponse:
    if store.get(task_id) is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    path = RESULT_DIR / f"{task_id}.{suffix}.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="结果图不存在")
    return FileResponse(path, media_type="image/png")


@app.get("/api/preview/{task_id}")
def preview(task_id: str) -> FileResponse:
    return _result_file(task_id, "detected")


@app.get("/api/heatmap/{task_id}")
def heatmap(task_id: str) -> FileResponse:
    return _result_file(task_id, "heatmap")
