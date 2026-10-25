# 基于无人机多光谱与 YOLOv11 的新疆棉田病虫害智能识别

**UAV-Multispectral Cotton Pest & Disease Detection**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](requirements.txt)
[![Ultralytics](https://img.shields.io/badge/YOLO-v11-red.svg)](https://docs.ultralytics.com/)
[![Status](https://img.shields.io/badge/status-in%20development-orange.svg)](#项目进度)

新疆大学大学生创新创业训练计划项目（自治区级）· 计算机科学与技术学院

> 传统棉田病虫害监测依赖人工巡查，存在发现滞后、施药粗放、效率低下三大痛点。本项目以无人机多光谱影像与 YOLOv11 目标检测算法为核心，构建一套**高精度、轻量化、可复现**的新疆棉田病虫害智能识别系统：整合 CottonInsect、CPD-YOLO 等公开数据集并模拟多光谱影像，在 YOLOv11 框架下设计 RGB 与多光谱特征深度融合的双流检测模型，最终交付支持上传检测、严重度分级、统计报表与分布热力图的线上仿真平台。

---

## 目录

- [研究对象](#研究对象)
- [仓库结构](#仓库结构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [数据集获取](#数据集获取)
- [训练与评估](#训练与评估)
- [项目进度](#项目进度)
- [团队](#团队)
- [贡献指南](#贡献指南)
- [引用](#引用)
- [许可证](#许可证)

## 研究对象

新疆棉田主要病虫害：蚜虫、双斑萤叶甲、牧草盲蝽、棉铃虫等虫害，以及黄萎病、细菌性角斑病、棉铃腐烂病、红腐病等病害；严重度按 0–3 级标准化分级标注（健康/轻度/中度/重度）。

## 仓库结构

| 目录 | 对应研究内容 | 文档 |
|------|-------------|------|
| `dataset/` | 数据集资源：CottonInsect VOC→YOLO 转换脚本、13 类标注文件、YOLO 配置 | [dataset/README.md](dataset/README.md) |
| `multispectral/` | 多光谱预处理：辐射定标、波段配准、植被指数（NDVI/SAVI/RDVI/NDRE）、GLCM 纹理特征 | [multispectral/README.md](multispectral/README.md) |
| `models/` | YOLOv11-RGBT 双流融合网络：通道/空间注意力、P3 中期融合、小目标增强 | [models/README.md](models/README.md) |
| `experiments/` | 消融实验与可视化：PR 曲线、混淆矩阵、热力图、单模态 vs 融合对比 | [experiments/README.md](experiments/README.md) |
| `platform/` | 线上仿真检测平台：后端推理服务 + 前端界面 + 报表/热力图 | [platform/README.md](platform/README.md) |
| `docs/` | 项目文档：研究计划、参考文献 | [docs/README.md](docs/README.md) |

```
.
├── README.md                 项目说明
├── requirements.txt          Python 依赖
├── CITATION.cff              引用信息
├── CONTRIBUTING.md           协作规范
├── LICENSE                   MIT 许可证
├── dataset/                  数据集与标注转换
├── multispectral/            多光谱预处理与特征提取
├── models/                   YOLOv11-RGBT 双流融合网络
├── experiments/              消融实验与结果可视化
├── platform/                 线上仿真检测平台
└── docs/                     项目文档（研究计划、参考文献）
```

## 环境要求

- Python ≥ 3.10
- PyTorch ≥ 2.1（GPU 训练需 CUDA ≥ 11.8）
- Ultralytics ≥ 8.3.0

```bash
pip install -r requirements.txt
```

## 快速开始

数据集部分已就绪（标注文件已随仓库发布，图像需自行获取，见下方[数据集获取](#数据集获取)）：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 按 dataset/README.md 放入 CottonInsect 图像（images/train|val|test）

# 3. 将 dataset/cotton_insect.yaml 中的 path 改为本机 dataset 目录的绝对路径

# 4. 训练基线 YOLOv11
yolo detect train data=dataset/cotton_insect.yaml model=yolo11n.pt epochs=100 imgsz=640
```

## 数据集获取

图像数据因版权与体积原因**不随仓库分发**，仅提供标注与转换脚本。获取与目录约定详见 [dataset/README.md](dataset/README.md)。

## 训练与评估

| 任务 | 命令 |
|------|------|
| 基线训练 | `yolo detect train data=dataset/cotton_insect.yaml model=yolo11n.pt epochs=100 imgsz=640` |
| 验证 | `yolo detect val data=dataset/cotton_insect.yaml model=runs/detect/train/weights/best.pt` |
| 推理 | `yolo detect predict model=<weights> source=<images> conf=0.25 save_txt=True` |

多光谱特征提取（NDVI/SAVI/RDVI/NDRE + GLCM 纹理）：

```bash
python multispectral/vegetation_indices.py --input <multispectral.tif> --outdir outputs/features
```

## 线上仿真平台

平台已提供可运行的推理服务骨架（权重缺失时自动进入 demo 模式）：

```bash
pip install fastapi "uvicorn[standard]" python-multipart

cd platform && uvicorn app:app --reload --port 8000
# 或：uvicorn --app-dir platform app:app --port 8000
```

启动后访问 <http://127.0.0.1:8000>：上传影像 → 检测框 / 严重度分级 → 统计报表与分布热力图。
接口与自测说明见 [platform/README.md](platform/README.md)。

## 项目进度

| 阶段 | 周期 | 内容 | 状态 |
|------|------|------|------|
| 一 | 第 1–16 周 | 文献调研、数据集整理与预处理、Linux + CUDA + PyTorch + Ultralytics 环境搭建 | 🚧 进行中 |
| 二 | 第 17–36 周 | 基线 YOLOv11 训练、多光谱融合模块开发、双流网络构建、消融实验与可视化 | ⏳ 待开展 |
| 三 | 第 37–46 周 | 后端推理服务与前端界面开发、系统联调与测试 | 🚧 骨架完成 |
| 四 | 第 47–52 周 | 结项材料准备 | ⏳ 待开展 |

详细研究目标、关键科学问题与预期成果见 [docs/research-plan.md](docs/research-plan.md)。

## 团队

| 角色 | 成员 | 分工 |
|------|------|------|
| 项目负责人 | 丁丹丹 | 统筹与技术方案 |
| 成员 | 胡馨月、马灵钰 | 数据与模型 |
| 成员 | 李然 | 平台开发 |
| 成员 | 张宇翔 | 文献与测试 |
| 指导教师 | 李莉 副教授 | 指导 |

## 贡献指南

欢迎提交 Issue / Pull Request。分支命名、提交信息格式与评审清单见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 引用

若本项目对你的研究或教学有帮助，请引用：

```bibtex
@software{ding2026cottonpest,
  title  = {基于无人机多光谱与 YOLOv11 的新疆棉田病虫害智能识别},
  author = {丁丹丹 and 胡馨月 and 马灵钰 and 李然 and 张宇翔},
  year   = {2026},
  url    = {https://github.com/dida123-dot/UAV-Multispectral-Cotton-Pest-Detection},
  note   = {新疆大学大学生创新创业训练计划项目（自治区级）}
}
```

机器可读的引用信息见 [CITATION.cff](CITATION.cff)。

## 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 开源理念

项目以"开源可复现"为核心理念，从数据集构建、模型训练到系统部署全链条开源。图像数据因版权与体积原因不随仓库分发，获取方式见 [dataset/README.md](dataset/README.md)。
