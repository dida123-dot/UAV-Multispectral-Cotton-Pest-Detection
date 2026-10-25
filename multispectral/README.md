# multispectral/ 多光谱预处理与特征提取

将无人机多光谱原始影像转换为与 RGB 对齐的特征张量，供 YOLOv11-RGBT 双流网络使用。

## 处理流程

| 步骤 | 内容 | 说明 |
|------|------|------|
| 1 | 辐射定标 | 原始 DN 值 → 表观反射率（经验线性定标，按相机标定系数） |
| 2 | 波段配准 | 以 NIR 波段为基准，对 Blue/Green/Red/RedEdge 做 ECC 亚像素配准 |
| 3 | 植被指数 | NDVI / SAVI / RDVI / NDRE，突出早期病害胁迫 |
| 4 | 纹理特征 | GLCM 对比度、同质性、能量、相关性（滑动窗口） |
| 5 | 特征堆叠 | RGB(3) + 指数(4) + 纹理(4) → 11 通道特征图，与标注框对齐后切片 |

## 使用

```bash
# 计算植被指数并输出 GeoTIFF，同时打印整幅影像的 GLCM 纹理统计
python multispectral/vegetation_indices.py --input scene.tif --outdir outputs/features \
    --nir 4 --red 3 --red-edge 5
```

默认波段顺序按常见 5 波段多光谱相机（Blue, Green, Red, NIR, RedEdge），如相机不同请用
`--nir/--red/--red-edge` 指定。

## 文件

| 文件 | 说明 |
|------|------|
| `vegetation_indices.py` | 植被指数与 GLCM 纹理特征提取（核心函数仅依赖 numpy） |

## 待补充

- [ ] 辐射定标系数表 `calibration.yaml`
- [ ] 波段配准脚本 `register.py`（ECC / 特征点法）
- [ ] 特征切片与增强脚本 `patchify.py`
- [ ] 多光谱模拟（RGB → NIR/RedEdge 合成）Baseline
