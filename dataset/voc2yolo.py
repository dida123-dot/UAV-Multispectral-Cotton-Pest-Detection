#!/usr/bin/env python
"""将 Pascal VOC 格式标注转换为 YOLO 格式，用于 CottonInsect 数据集。

示例：
    python dataset/voc2yolo.py \
        --annotations CottonInsect/Annotations \
        --images CottonInsect/JPEGImages \
        --out dataset --split train --copy-images

输出：
    dataset/labels/<split>/*.txt   YOLO 标签（cls cx cy w h，归一化）
    dataset/images/<split>/*      仅当指定 --copy-images 时复制图像
"""

from __future__ import annotations

import argparse
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import yaml


def load_class_names(yaml_path: Path) -> dict[str, int]:
    with yaml_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return {name: idx for idx, name in cfg["names"].items()}


def convert_annotation(
    xml_path: Path,
    class_map: dict[str, int],
    skip_difficult: bool = True,
) -> tuple[list[str], Counter]:
    root = ET.parse(xml_path).getroot()
    size = root.find("size")
    width = float(size.findtext("width"))
    height = float(size.findtext("height"))
    if width <= 0 or height <= 0:
        raise ValueError(f"{xml_path.name}: 图像尺寸非法 ({width}x{height})")

    lines: list[str] = []
    stats: Counter = Counter()
    for obj in root.findall("object"):
        name = (obj.findtext("name") or "").strip()
        if name not in class_map:
            stats[f"unknown:{name}"] += 1
            continue
        if skip_difficult and obj.findtext("difficult") == "1":
            stats["difficult"] += 1
            continue

        box = obj.find("bndbox")
        xmin, ymin, xmax, ymax = (float(box.findtext(k)) for k in ("xmin", "ymin", "xmax", "ymax"))
        xmin, xmax = max(0.0, min(xmin, xmax)), min(width, max(xmin, xmax))
        ymin, ymax = max(0.0, min(ymin, ymax)), min(height, max(ymin, ymax))
        w, h = xmax - xmin, ymax - ymin
        if w <= 1 or h <= 1:
            stats["degenerate"] += 1
            continue

        cx, cy = (xmin + xmax) / 2 / width, (ymin + ymax) / 2 / height
        lines.append(f"{class_map[name]} {cx:.6f} {cy:.6f} {w / width:.6f} {h / height:.6f}")
        stats[name] += 1
    return lines, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="VOC -> YOLO 标注转换")
    parser.add_argument("--annotations", required=True, type=Path, help="VOC Annotations 目录")
    parser.add_argument("--images", required=True, type=Path, help="图像目录")
    parser.add_argument("--out", default=Path("dataset"), type=Path, help="输出 dataset 根目录")
    parser.add_argument("--split", default="train", choices=["train", "val", "test"], help="数据划分")
    parser.add_argument(
        "--yaml",
        default=Path(__file__).with_name("cotton_insect.yaml"),
        type=Path,
        help="类别配置文件",
    )
    parser.add_argument("--copy-images", action="store_true", help="同时复制图像到 dataset/images/<split>")
    parser.add_argument("--keep-difficult", action="store_true", help="保留 difficult=1 的目标")
    args = parser.parse_args()

    class_map = load_class_names(args.yaml)
    label_dir = args.out / "labels" / args.split
    image_dir = args.out / "images" / args.split
    label_dir.mkdir(parents=True, exist_ok=True)
    if args.copy_images:
        image_dir.mkdir(parents=True, exist_ok=True)

    xml_files = sorted(args.annotations.glob("*.xml"))
    if not xml_files:
        raise SystemExit(f"未在 {args.annotations} 找到任何 .xml 标注")

    total: Counter = Counter()
    converted = skipped = 0
    for xml_path in xml_files:
        lines, stats = convert_annotation(xml_path, class_map, not args.keep_difficult)
        total.update(stats)
        if not lines:
            skipped += 1
            continue
        (label_dir / f"{xml_path.stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        converted += 1
        if args.copy_images:
            src = next((p for p in args.images.glob(f"{xml_path.stem}.*")), None)
            if src is None:
                total["missing_image"] += 1
            else:
                shutil.copy2(src, image_dir / src.name)

    print(f"转换完成：{converted} 个文件写入 {label_dir}")
    if skipped:
        print(f"跳过 {skipped} 个无有效目标（或全为 difficult）的标注")
    for key, value in sorted(total.items()):
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
