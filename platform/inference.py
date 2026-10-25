"""推理服务：封装 YOLOv11 权重加载与预测。

权重缺失时进入 demo 模式（由图像内容确定性地生成伪检测框），
保证平台在没有训练产物时也能独立启动、联调与演示。
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

DEMO_CLASSES = ["aphid", "flea_beetle", "plant_bug", "bollworm", "verticillium_wilt"]


@dataclass
class Detection:
    cls_id: int
    cls_name: str
    conf: float
    bbox: list[int]  # xmin, ymin, xmax, ymax

    def to_dict(self) -> dict:
        return asdict(self)


class Detector:
    def __init__(self, weights: str | Path | None = None, conf: float = 0.25):
        self.weights = Path(weights) if weights else None
        self.conf = conf
        self._model = None
        self.class_names: dict[int, str] = dict(enumerate(DEMO_CLASSES))

    @property
    def mode(self) -> str:
        return "demo" if self._model is None else f"model:{self.weights.name}"

    def load(self) -> "Detector":
        if self.weights is None or not self.weights.exists():
            return self
        from ultralytics import YOLO

        self._model = YOLO(str(self.weights))
        names = getattr(self._model, "names", None) or {}
        if names:
            self.class_names = {int(k): str(v) for k, v in names.items()}
        return self

    def predict(self, image: np.ndarray) -> list[Detection]:
        if self._model is None:
            return self._demo_predict(image)

        result = self._model.predict(image, conf=self.conf, verbose=False)[0]
        detections: list[Detection] = []
        for box in result.boxes:
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            cls_id = int(box.cls.item())
            detections.append(
                Detection(
                    cls_id=cls_id,
                    cls_name=self.class_names.get(cls_id, str(cls_id)),
                    conf=round(float(box.conf.item()), 4),
                    bbox=[x1, y1, x2, y2],
                )
            )
        return detections

    def _demo_predict(self, image: np.ndarray) -> list[Detection]:
        height, width = image.shape[:2]
        seed = hashlib.sha256(image.tobytes()).digest()[:8]
        rng = np.random.default_rng(int.from_bytes(seed, "big"))
        detections: list[Detection] = []
        for _ in range(int(rng.integers(0, 4))):
            bw = int(rng.integers(max(2, width // 20), max(3, width // 6)))
            bh = int(rng.integers(max(2, height // 20), max(3, height // 6)))
            x1 = int(rng.integers(0, max(1, width - bw)))
            y1 = int(rng.integers(0, max(1, height - bh)))
            cls_id = int(rng.integers(0, len(self.class_names)))
            detections.append(
                Detection(
                    cls_id=cls_id,
                    cls_name=self.class_names[cls_id],
                    conf=round(float(rng.uniform(0.35, 0.95)), 4),
                    bbox=[x1, y1, x1 + bw, y1 + bh],
                )
            )
        return detections


def load_image(data: bytes) -> np.ndarray:
    from PIL import Image

    return np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))
