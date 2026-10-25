"""严重度分级：检测框面积占比 + 植被指数。

分级标准（0–3 级）：
    0 健康 —— 无检测目标
    1 轻度 —— 单目标面积占比 < 0.5%
    2 中度 —— 0.5% ~ 2%
    3 重度 —— > 2%
植被指数偏低（长势受抑）时上调一级，最高仍为 3 级。
"""

from __future__ import annotations

from collections import Counter

import numpy as np

SEVERITY_LABELS = {0: "健康", 1: "轻度", 2: "中度", 3: "重度"}

MILD_RATIO = 0.005
MODERATE_RATIO = 0.02
LOW_VIGOUR = 0.02  # ExG 均值低于该值视为长势受抑（待用真实 NDVI 标定）


def visible_vegetation_index(image: np.ndarray) -> float:
    """RGB 影像上的可见光植被指数 ExG 归一化值，作为 NDVI 的近似代理。

    有真实多光谱数据时请改用 multispectral/vegetation_indices.py 计算的 NDVI。
    """
    rgb = image.astype(np.float32)
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    exg = (2 * green - red - blue) / (red + green + blue + 1e-6)
    return round(float(np.clip(exg.mean(), -1.0, 1.0)), 4)


def grade(area_ratio: float, veg_index: float | None = None) -> int:
    if area_ratio <= 0:
        return 0
    if area_ratio < MILD_RATIO:
        level = 1
    elif area_ratio < MODERATE_RATIO:
        level = 2
    else:
        level = 3
    if veg_index is not None and veg_index < LOW_VIGOUR and level < 3:
        level += 1
    return level


def summarize(detections: list[dict], image_shape: tuple[int, int], veg_index: float | None = None) -> dict:
    height, width = image_shape
    image_area = float(height * width) or 1.0

    graded: list[dict] = []
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        area_ratio = max(0.0, (x2 - x1) * (y2 - y1)) / image_area
        item = dict(det)
        item["area_ratio"] = round(area_ratio, 6)
        item["severity"] = grade(area_ratio, veg_index)
        item["severity_label"] = SEVERITY_LABELS[item["severity"]]
        graded.append(item)

    severity_dist = {str(level): 0 for level in SEVERITY_LABELS}
    for item in graded:
        severity_dist[str(item["severity"])] += 1
    class_counts = Counter(item["cls_name"] for item in graded)

    return {
        "detections": graded,
        "summary": {
            "total": len(graded),
            "severity_dist": severity_dist,
            "class_counts": dict(class_counts),
            "veg_index": veg_index,
        },
    }
