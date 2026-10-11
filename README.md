# experiments — 消融实验与分析

对应申报书第二阶段（第 17–36 周）：

- 单模态 vs 融合消融：RGB-only / 多光谱-only / RGB+MS 早期融合 / RGB+MS 中期融合
- 指标：Precision、Recall、mAP@50、mAP@50-95、F1、参数量、FPS
- 可视化：PR 曲线、混淆矩阵、特征热力图（Grad-CAM）验证敏感波段贡献
- 严重度分级检测评估：0–3 级分级准确率

实验配置与结果统一存放于本目录（`runs/` 已在 .gitignore 排除）。
