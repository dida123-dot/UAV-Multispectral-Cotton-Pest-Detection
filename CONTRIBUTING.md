# 贡献指南

感谢参与本项目。以下约定保证实验结果可复现、提交历史可追溯。

## 分支约定

| 分支 | 用途 |
|------|------|
| `main` | 可复现的稳定版本，仅通过 PR 合入 |
| `feat/<主题>` | 新功能，如 `feat/multispectral-fusion` |
| `fix/<主题>` | 缺陷修复，如 `fix/yolo-dataloader` |
| `exp/<编号>-<主题>` | 实验性改动，如 `exp/03-p3-fusion` |

## 提交信息

采用 [Conventional Commits](https://www.conventionalcommits.org/)：

```text
<type>(<scope>): <简短描述>

feat(models): 增加 CBAM 通道注意力模块
fix(dataset): 修复 VOC 转换漏检 difficult 目标的问题
docs(readme): 补充数据集获取说明
```

`type` 取值：`feat` / `fix` / `docs` / `exp` / `refactor` / `test` / `chore`。

## 代码规范

- Python 遵循 PEP 8，行宽 100，建议使用 `ruff` + `black`：
  ```bash
  pip install ruff black
  ruff check . && black --line-length 100 .
  ```
- 每个脚本需提供 `--help` 与参数说明，避免硬编码路径。
- 随机种子、模型权重版本、数据集版本必须在实验记录中注明。

## 禁止提交的内容

- 数据集原始图像（版权与体积原因，见 `.gitignore`）
- 模型权重文件（`*.pt` / `*.pth` / `*.onnx` / `*.engine`）
- 训练输出目录 `runs/`、`wandb/`、`outputs/`
- 任何密钥、`.env` 文件、服务器账号

## Pull Request 清单

- [ ] 已通过 `ruff check .` 与 `python -m compileall .`
- [ ] 若涉及模型改动，附上验证集指标（mAP50 / mAP50-95 / 参数量 / FPS）
- [ ] 若新增实验，结果图放入 `experiments/` 并在对应 README 登记
- [ ] 已更新相关文档
- [ ] 未包含数据集图像与权重文件

## Issue

请使用仓库的 Issue 模板提交缺陷或建议；涉及数据集/环境问题请附 `python -c "import torch;print(torch.__version__, torch.cuda.is_available())"` 输出。
