#!/usr/bin/env python
"""数据集完整性校验：类别配置 ⇄ 标注文件 ⇄ 图像 三者一致性。

检查项：
1. cotton_insect.yaml 的 nc 与 names 数量一致；
2. 标签文件每行的类别 id 在 [0, nc) 内，坐标已归一化到 (0, 1]；
3. 每个标签文件都能找到同名图像（按 --image-ext 匹配）；
4. 类别名仍为 class_XX 占位（未核对官方类目）时给出告警。

示例：
    python dataset/check_dataset.py --root dataset --splits train val test
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import yaml

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YOLO 数据集一致性校验")
    parser.add_argument("--root", default=Path("dataset"), type=Path, help="dataset 根目录")
    parser.add_argument(
        "--yaml",
        default=Path(__file__).with_name("cotton_insect.yaml"),
        type=Path,
        help="类别配置文件",
    )
    parser.add_argument("--splits", nargs="+", default=["train", "val", "test"])
    parser.add_argument("--strict", action="store_true", help="存在占位类别名时以非零码退出")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.yaml.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    num_classes = int(cfg["nc"])
    names = {int(k): str(v) for k, v in cfg["names"].items()}
    errors: list[str] = []
    warnings: list[str] = []

    if len(names) != num_classes:
        errors.append(f"nc={num_classes} 与 names 数量 {len(names)} 不一致")
    if sorted(names) != list(range(num_classes)):
        errors.append(f"类别 id 必须为 0..{num_classes - 1} 连续整数，当前为 {sorted(names)}")

    placeholders = [f"{i}:{n}" for i, n in sorted(names.items()) if n.startswith("class_")]
    if placeholders:
        warnings.append(f"{len(placeholders)} 个类别仍为占位名，需按官方类目核对：{', '.join(placeholders)}")

    total_boxes: Counter = Counter()
    for split in args.splits:
        label_dir = args.root / "labels" / split
        image_dir = args.root / "images" / split
        if not label_dir.exists():
            warnings.append(f"{split}: 标签目录不存在（{label_dir}）")
            continue

        images = {p.stem for p in image_dir.glob("*") if p.suffix.lower() in IMAGE_EXTS}
        labels = sorted(label_dir.glob("*.txt"))
        if not labels:
            warnings.append(f"{split}: 没有标签文件")
        for label_path in labels:
            if not images:
                errors.append(f"{split}: 图像目录为空，无法与 {label_path.name} 配对")
                break
            if label_path.stem not in images:
                errors.append(f"{split}: 缺少与 {label_path.name} 对应的图像")
            for lineno, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), 1):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 5:
                    errors.append(f"{split}/{label_path.name}:{lineno} 字段数应为 5，实际 {len(parts)}")
                    continue
                try:
                    cls_id = int(parts[0])
                    coords = [float(v) for v in parts[1:]]
                except ValueError:
                    errors.append(f"{split}/{label_path.name}:{lineno} 含非数字内容")
                    continue
                if not 0 <= cls_id < num_classes:
                    errors.append(f"{split}/{label_path.name}:{lineno} 类别 id {cls_id} 越界")
                if any(not 0.0 <= v <= 1.0 for v in coords):
                    errors.append(f"{split}/{label_path.name}:{lineno} 坐标未归一化到 [0,1]")
                if coords[2] <= 0 or coords[3] <= 0:
                    errors.append(f"{split}/{label_path.name}:{lineno} 宽或高为 0")
                total_boxes[names.get(cls_id, str(cls_id))] += 1

    for message in warnings:
        print(f"[WARN] {message}")
    for message in errors[:30]:
        print(f"[ERROR] {message}")
    if len(errors) > 30:
        print(f"[ERROR] ... 另有 {len(errors) - 30} 条错误未显示")

    print(f"\n类别数: {num_classes}；目标框总数: {sum(total_boxes.values())}")
    for name, count in total_boxes.most_common():
        print(f"  {name}: {count}")

    if errors:
        print(f"\n校验失败：{len(errors)} 个错误")
        return 1
    if placeholders and args.strict:
        print("\n校验未通过：存在占位类别名（--strict）")
        return 2
    print("\n校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
