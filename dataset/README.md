# dataset/ 数据集资源

本目录存放 CottonInsect 等公开数据集的**标注转换脚本、类别配置**；原始图像不入库。

## 目录结构（转换后）

```text
dataset/
├── cotton_insect.yaml     # YOLOv11 数据集配置（需改 path 为绝对路径）
├── voc2yolo.py            # VOC XML -> YOLO txt 转换脚本
├── images/
│   ├── train/             # 训练图像（自行获取，不入库）
│   ├── val/
│   └── test/
└── labels/
    ├── train/             # YOLO 标签：cls cx cy w h（归一化）
    ├── val/
    └── test/
```

## 数据来源

| 数据集 | 说明 | 获取方式 |
|--------|------|----------|
| CottonInsect | 棉田害虫检测数据集，VOC 格式标注，含 13 类 | 按官方发布页申请/下载后放入本地 `CottonInsect/` |
| CPD-YOLO | 补充病虫害类别与复杂背景样本 | 同上 |
| 多光谱模拟影像 | 由 RGB 合成 NIR/RedEdge 波段，用于融合训练 | 见 `multispectral/` |

> 图像因版权与体积原因不随仓库分发，仓库仅保留标注与转换脚本。

## 类别与严重度

- **13 类**病虫害，类别顺序见 `cotton_insect.yaml`（0–7 类已固定，8–12 待核对官方类目后重命名）。
- 严重度按 **0–3 级**标注（健康 / 轻度 / 中度 / 重度）；分级结果由检测框面积占比 + 光谱指数联合判定，用于平台统计报表。

## 转换流程

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. VOC -> YOLO（每个 split 执行一次）
python dataset/voc2yolo.py --annotations CottonInsect/Annotations --images CottonInsect/JPEGImages \
    --out dataset --split train --copy-images
python dataset/voc2yolo.py --annotations CottonInsect/Annotations --images CottonInsect/JPEGImages \
    --out dataset --split val --copy-images

# 3. 修改 cotton_insect.yaml 中 path 为本机 dataset 绝对路径

# 4. 校验数据集并开始训练
yolo detect train data=dataset/cotton_insect.yaml model=yolo11n.pt epochs=100 imgsz=640
```

脚本行为：
- 自动跳过 `difficult=1` 目标（可用 `--keep-difficult` 保留）；
- 未知类别名计入统计并跳过，不会静默写入错误标签；
- 退化框（宽或高 ≤ 1 像素）与缺失图像会被统计输出。
