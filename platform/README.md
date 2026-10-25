# platform/ 线上仿真检测平台

面向演示与验收的 Web 检测平台：上传影像 → 模型推理 → 类型/置信度/位置/严重度分级 → 统计报表与分布热力图。

## 功能状态

| 模块 | 功能 | 状态 |
|------|------|------|
| 影像上传 | 单张 / 批量上传，支持 jpg / png / tif | ✅ 已实现 |
| 检测推理 | 调用 YOLOv11 权重；权重缺失时进入 demo 模式 | ✅ 已实现 |
| 严重度分级 | 框面积占比 + 植被指数，0–3 级 | ✅ 已实现 |
| 统计报表 | 类别计数、严重度分布、JSON 报表 | ✅ 已实现 |
| 分布热力图 | 检测密度网格 → 高斯平滑 → JET 着色 | ✅ 已实现 |
| 历史记录 | SQLite 任务表 + 前端列表 | ✅ 已实现 |
| 鉴权 / 多用户 | 登录、任务隔离 | ⏳ 未实现 |
| 导出 CSV / PDF | 报表导出 | ⏳ 未实现 |

## 目录

```text
platform/
├── app.py            FastAPI 入口（路由、上传校验、结果落盘）
├── inference.py      Detector：权重加载 + 推理；demo 模式伪检测
├── severity.py       严重度分级（面积占比 + ExG 植被指数）
├── storage.py        SQLite 任务与检测记录
├── visualize.py      检测框绘制、分布热力图
├── templates/        Jinja2 页面
├── static/           样式
├── test_api.py       接口自测（无需真实权重）
├── weights/          本地权重目录（不入库）
└── data/             tasks.db 与结果图（不入库）
```

## 启动

```bash
pip install -r requirements.txt

# 方式一：在 platform 目录下运行
cd platform && uvicorn app:app --reload --port 8000

# 方式二：在仓库根目录运行
uvicorn --app-dir platform app:app --port 8000
```

> 目录名 `platform` 与 Python 标准库模块同名。本目录**不含 `__init__.py`**，
> 因此标准库 `platform` 仍可正常导入（`ultralytics`/`torch` 依赖它）。
> 请勿按包的方式导入 `platform.app`，使用上述两种启动方式之一。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `YOLO_WEIGHTS` | `platform/weights/best.pt` | 权重路径；文件不存在则进入 demo 模式 |
| `YOLO_CONF` | `0.25` | 置信度阈值 |
| `PLATFORM_DATA_DIR` | `platform/data` | SQLite 与结果图目录 |
| `MAX_UPLOAD_MB` | `20` | 单文件大小上限 |

## 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 平台首页（上传 + 历史任务） |
| `GET` | `/health` | 健康检查：推理模式、类别列表 |
| `POST` | `/api/detect` | 单张检测，返回类型、置信度、位置、严重度 |
| `POST` | `/api/detect/batch` | 批量检测（字段名 `files`） |
| `GET` | `/api/tasks?limit=20` | 任务历史 |
| `GET` | `/api/report/{task_id}` | 统计报表（类别计数 + 严重度分布） |
| `GET` | `/api/preview/{task_id}` | 检测结果图（PNG） |
| `GET` | `/api/heatmap/{task_id}` | 分布热力图（PNG） |

检测响应示例：

```json
{
  "task_id": "20261025-082952-9245ab",
  "image": "field_01.jpg",
  "model": "demo",
  "size": {"width": 200, "height": 160},
  "detections": [
    {"cls_id": 0, "cls_name": "aphid", "conf": 0.7764,
     "bbox": [55, 98, 69, 119], "area_ratio": 0.009187,
     "severity": 3, "severity_label": "重度"}
  ],
  "summary": {
    "total": 1,
    "severity_dist": {"0": 0, "1": 0, "2": 0, "3": 1},
    "class_counts": {"aphid": 1},
    "veg_index": -0.0017
  },
  "urls": {"preview": "/api/preview/...", "heatmap": "/api/heatmap/...", "report": "/api/report/..."}
}
```

## 严重度分级

| 级别 | 名称 | 单目标面积占比 |
|------|------|----------------|
| 0 | 健康 | 无检出目标 |
| 1 | 轻度 | < 0.5% |
| 2 | 中度 | 0.5% – 2% |
| 3 | 重度 | > 2% |

植被指数（RGB 影像上的 ExG 归一化值）低于阈值时上调一级，最高 3 级。
`ExG` 是 NDVI 的可见光近似，拿到真实多光谱数据后应改用
`multispectral/vegetation_indices.py` 计算的 NDVI，并按数据集标定阈值。

## 自测

```bash
cd platform && python test_api.py
```

覆盖：`/health`、首页渲染、单张/批量检测、报表、结果图、`/api/tasks` 计数，以及
404 / 空文件 / 非法图像三类错误路径。测试使用临时数据目录，不污染本地 `data/`。

## 待补充

- [ ] 接入真实权重并与 `models/` 双流网络联调
- [ ] 报表导出 CSV / PDF
- [ ] 登录鉴权与任务归属
- [ ] Docker 部署与 Nginx 反向代理说明
