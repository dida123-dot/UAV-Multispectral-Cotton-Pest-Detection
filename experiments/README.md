# experiments/ 消融实验与结果可视化

## 实验矩阵

| 编号 | 配置 | 输入 | 融合位置 | 注意力 | 小目标头 | mAP50 | mAP50-95 | 参数量(M) | FPS |
|------|------|------|----------|--------|----------|-------|----------|-----------|-----|
| E0 | YOLOv11n 基线 | RGB | — | ✗ | ✗ | — | — | — | — |
| E1 | 多光谱单模态 | NDVI/NDRE 等 | — | ✗ | ✗ | — | — | — | — |
| E2 | 早期融合 | RGB+MSS | Backbone 输入 | ✗ | ✗ | — | — | — | — |
| E3 | 中期融合（P3） | RGB+MSS | P3 | ✗ | ✗ | — | — | — | — |
| E4 | 中期融合 + CBAM | RGB+MSS | P3 | ✓ | ✗ | — | — | — | — |
| E5 | 中期融合 + CBAM + P2 头 | RGB+MSS | P3 | ✓ | ✓ | — | — | — | — |

> 表格在实验完成后填写；每行须注明训练配置文件名与随机种子，保证可复现。

## 可视化产物约定

| 类型 | 文件名 | 生成方式 |
|------|--------|----------|
| PR 曲线 | `pr_curve_<exp>.png` | Ultralytics `val` 输出 + matplotlib 重绘 |
| 混淆矩阵 | `confusion_matrix_<exp>.png` | `yolo detect val ... plots=True` |
| 检测结果对比 | `compare_<exp>.png` | 基线 vs 融合模型的并排检测框 |
| 特征热力图 | `heatmap_<exp>.png` | Grad-CAM / EigenCAM |
| 病害分布热力图 | `distribution_heatmap.png` | 平台统计模块输出的田块级分布 |

## 日志规范

```text
experiments/
├── E3_p3_fusion/
│   ├── args.yaml        # 训练参数快照（Ultralytics 自动生成）
│   ├── results.csv      # 逐 epoch 指标
│   ├── pr_curve.png
│   └── notes.md         # 结论与异常记录
```

训练结果目录 `runs/` 已被 `.gitignore` 忽略，仅将上述选定图表与结论提交入库。
