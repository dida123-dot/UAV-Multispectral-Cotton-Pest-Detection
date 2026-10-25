"""结果可视化：检测框绘制与分布热力图。"""

from __future__ import annotations

import numpy as np

SEVERITY_COLORS = {  # RGB
    0: (34, 197, 94),
    1: (250, 204, 21),
    2: (249, 115, 22),
    3: (220, 38, 38),
}


def draw_detections(image: np.ndarray, detections: list[dict], thickness: int = 2) -> np.ndarray:
    import cv2

    canvas = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        color = SEVERITY_COLORS.get(det.get("severity", 0), (255, 255, 255))[::-1]
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, thickness)
        label = f"{det['cls_name']} {det['conf']:.2f} L{det.get('severity', 0)}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(canvas, (x1, max(0, y1 - th - 6)), (x1 + tw + 4, y1), color, -1)
        cv2.putText(
            canvas, label, (x1 + 2, max(10, y1 - 5)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA,
        )
    return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)


def build_heatmap(
    image_shape: tuple[int, int],
    detections: list[dict],
    grid: int = 16,
    sigma: float = 1.2,
) -> np.ndarray:
    """把检测框中心累积成网格密度图，再上采样并着色，输出 RGB 数组。"""
    import cv2

    height, width = image_shape
    grid = max(2, min(grid, min(height, width) or 2))
    density = np.zeros((grid, grid), dtype=np.float32)
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        gx = min(grid - 1, max(0, int(cx / max(width, 1) * grid)))
        gy = min(grid - 1, max(0, int(cy / max(height, 1) * grid)))
        weight = float(det.get("conf", 1.0)) * (1 + det.get("severity", 0))
        density[gy, gx] += weight

    if density.max() > 0:
        density = cv2.GaussianBlur(density, (3, 3), sigma)
        density /= density.max()
    colored = cv2.applyColorMap((density * 255).astype(np.uint8), cv2.COLORMAP_JET)
    colored = cv2.resize(colored, (width, height), interpolation=cv2.INTER_NEAREST)
    return cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
