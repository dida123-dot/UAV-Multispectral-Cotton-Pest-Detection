"""多光谱植被指数与纹理特征提取。

核心函数仅依赖 numpy；读写 GeoTIFF 时才需要 rasterio。

用法：
    python multispectral/vegetation_indices.py --input scene.tif --outdir outputs/features
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

EPS = 1e-6


def _safe_ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    return num / (den + EPS)


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """归一化植被指数，反映绿度与生物量。"""
    return _safe_ratio(nir - red, nir + red)


def savi(nir: np.ndarray, red: np.ndarray, soil_factor: float = 0.5) -> np.ndarray:
    """土壤调节植被指数，抑制裸土背景影响。"""
    return _safe_ratio((nir - red) * (1 + soil_factor), nir + red + soil_factor)


def rdvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """重归一化差值植被指数，兼顾高/低植被覆盖区。"""
    return _safe_ratio(nir - red, np.sqrt(nir + red))


def ndre(nir: np.ndarray, red_edge: np.ndarray) -> np.ndarray:
    """归一化红边指数，对早期病害胁迫敏感。"""
    return _safe_ratio(nir - red_edge, nir + red_edge)


def glcm_texture(band: np.ndarray, quantize_levels: int = 32, distance: int = 1) -> dict[str, np.ndarray]:
    """在灰度量化后的波段上计算 GLCM 纹理特征（对比度/同质性/能量/相关性）。"""
    from skimage.feature import graycomatrix, graycoprops

    quantized = np.clip(band.astype(np.float32), 0, None)
    peak = quantized.max() or 1.0
    quantized = (quantized / peak * (quantize_levels - 1)).astype(np.uint8)

    matrix = graycomatrix(
        quantized,
        distances=[distance],
        angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
        levels=quantize_levels,
        symmetric=True,
        normed=True,
    )
    return {
        prop: graycoprops(matrix, prop).mean(axis=1)[0]
        for prop in ("contrast", "homogeneity", "energy", "correlation")
    }


def compute_all(nir: np.ndarray, red: np.ndarray, red_edge: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "NDVI": ndvi(nir, red),
        "SAVI": savi(nir, red),
        "RDVI": rdvi(nir, red),
        "NDRE": ndre(nir, red_edge),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="多光谱植被指数 / GLCM 纹理特征提取")
    parser.add_argument("--input", required=True, type=Path, help="多波段 GeoTIFF")
    parser.add_argument("--outdir", default=Path("outputs/features"), type=Path)
    parser.add_argument("--nir", type=int, default=4, help="近红外波段序号（1 起）")
    parser.add_argument("--red", type=int, default=3, help="红光波段序号")
    parser.add_argument("--red-edge", type=int, default=5, help="红边波段序号")
    args = parser.parse_args()

    import rasterio

    args.outdir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(args.input) as src:
        meta = src.meta.copy()
        nir = src.read(args.nir).astype(np.float32)
        red = src.read(args.red).astype(np.float32)
        red_edge = src.read(args.red_edge).astype(np.float32)
        profile = {**meta, "count": 1, "dtype": "float32"}

    features = compute_all(nir, red, red_edge)
    for name, array in features.items():
        dst = args.outdir / f"{name}.tif"
        with rasterio.open(dst, "w", **profile) as writer:
            writer.write(array.astype(np.float32), 1)
        print(f"{name}: min={array.min():.4f} max={array.max():.4f} mean={array.mean():.4f} -> {dst}")

    texture = glcm_texture(nir)
    for name, value in texture.items():
        print(f"GLCM {name}: {value:.4f}")


if __name__ == "__main__":
    main()
