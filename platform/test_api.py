"""平台接口自测（无需真实权重，走 demo 模式）。

运行：
    cd platform && python test_api.py
"""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import numpy as np


def make_image(width: int = 160, height: int = 120, seed: int = 0) -> bytes:
    from PIL import Image

    rng = np.random.default_rng(seed)
    array = rng.integers(60, 200, size=(height, width, 3), dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(array, "RGB").save(buffer, format="PNG")
    return buffer.getvalue()


def main() -> None:
    import os

    tmp = tempfile.mkdtemp(prefix="platform-test-")
    os.environ["PLATFORM_DATA_DIR"] = tmp
    os.environ["YOLO_WEIGHTS"] = str(Path(tmp) / "missing.pt")

    from fastapi.testclient import TestClient

    import app as app_module

    app_module.detector.load()
    client = TestClient(app_module.app)

    health = client.get("/health").json()
    assert health["status"] == "ok" and health["model"] == "demo", health
    print(f"health ok, demo classes={len(health['classes'])}")

    page = client.get("/")
    assert page.status_code == 200 and "新疆棉田病虫害" in page.text
    print("index page ok")

    resp = client.post(
        "/api/detect", files={"file": ("field_01.png", make_image(), "image/png")}
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()
    task_id = result["task_id"]
    assert result["summary"]["total"] == len(result["detections"])
    assert set(result["summary"]["severity_dist"]) == {"0", "1", "2", "3"}
    for det in result["detections"]:
        assert 0 <= det["severity"] <= 3
    print(f"detect ok task={task_id} total={result['summary']['total']} veg={result['summary']['veg_index']}")

    batch = client.post(
        "/api/detect/batch",
        files=[
            ("files", ("a.png", make_image(seed=1), "image/png")),
            ("files", ("b.png", make_image(seed=2), "image/png")),
        ],
    )
    assert batch.status_code == 200 and batch.json()["count"] == 2, batch.text
    print("batch ok")

    report = client.get(f"/api/report/{task_id}")
    assert report.status_code == 200 and report.json()["task_id"] == task_id
    print("report ok")

    for url in (result["urls"]["preview"], result["urls"]["heatmap"]):
        img = client.get(url)
        assert img.status_code == 200 and img.headers["content-type"] == "image/png", url
    print("preview/heatmap ok")

    assert client.get("/api/report/not-exist").status_code == 404
    assert client.post("/api/detect", files={"file": ("x.png", b"", "image/png")}).status_code == 400
    assert client.post("/api/detect", files={"file": ("x.png", b"not-an-image", "image/png")}).status_code == 400
    print("error handling ok (404 / empty / bad image)")

    tasks = client.get("/api/tasks").json()["tasks"]
    assert len(tasks) == 3, tasks
    print(f"tasks ok: {len(tasks)} records")
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
