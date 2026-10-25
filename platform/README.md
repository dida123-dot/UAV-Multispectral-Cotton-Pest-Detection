# platform/ 线上仿真检测平台

面向演示与验收的 Web 检测平台：上传影像 → 模型推理 → 类型/置信度/位置/严重度分级 → 统计报表与分布热力图。

## 功能清单

| 模块 | 功能 | 状态 |
|------|------|------|
| 影像上传 | 单张 / 批量上传，支持 jpg/png/tif | 待开发 |
| 检测推理 | 调用 YOLOv11-RGBT 权重，返回框、类别、置信度 | 待开发 |
| 严重度分级 | 依据框面积占比 + 植被指数，按 0–3 级标注 | 待开发 |
| 统计报表 | 类别计数、严重度分布、导出 CSV | 待开发 |
| 分布热力图 | 叠加检测密度图，定位病害聚集区 | 待开发 |
| 历史记录 | 检测任务列表与结果回看 | 待开发 |

## 技术栈

- 后端：FastAPI + Uvicorn，推理复用 `models/` 训练产物
- 前端：HTML + Jinja2 模板（或轻量 SPA）
- 存储：SQLite（检测记录）/ 本地文件（上传影像与结果图）

## 计划接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 平台首页 |
| `POST` | `/api/detect` | 上传单张影像，返回检测结果 JSON |
| `POST` | `/api/detect/batch` | 批量检测 |
| `GET` | `/api/report/{task_id}` | 统计报表（类别/严重度分布） |
| `GET` | `/api/heatmap/{task_id}` | 分布热力图 |
| `GET` | `/api/tasks` | 检测任务历史 |

检测响应示例：

```json
{
  "task_id": "20261011-0001",
  "image": "field_01.jpg",
  "detections": [
    {"class": "bollworm", "conf": 0.87, "bbox": [120, 84, 196, 158], "severity": 2}
  ],
  "summary": {"total": 1, "severity_dist": {"0": 0, "1": 0, "2": 1, "3": 0}}
}
```

## 本地启动（规划）

```bash
pip install -r requirements.txt
uvicorn platform.app:app --reload --port 8000
```

## 待补充

- [ ] `app.py` 推理服务骨架
- [ ] `templates/` 前端页面
- [ ] `static/` 样式与图表脚本
- [ ] 部署说明（Docker / 服务器）
