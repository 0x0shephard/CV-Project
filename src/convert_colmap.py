"""Convert COLMAP text outputs to viewer bundle (data.json, model.ply, images)."""

from __future__ import annotations

import json
from pathlib import Path
from shutil import copy2
from typing import Dict, List, Tuple

import numpy as np
from scipy.spatial.transform import Rotation


# Defaults can be adjusted at runtime if importing this module
INPUT_DIR = Path("calibration")
IMAGE_DIR = Path("Data/boulders")
OUTPUT_DIR = Path("viewer/assets")


def qvec_to_rotmat(qvec: np.ndarray) -> np.ndarray:
    """Convert COLMAP quaternion [qw, qx, qy, qz] to rotation matrix."""
    return Rotation.from_quat([qvec[1], qvec[2], qvec[3], qvec[0]]).as_matrix()


def parse_images_txt(path: Path) -> Dict[int, dict]:
    images = {}
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        parts = line.split()
        if len(parts) < 10:
            i += 1
            continue
        img_id = int(parts[0])
        qvec = np.array([float(x) for x in parts[1:5]], dtype=float)
        tvec = np.array([float(x) for x in parts[5:8]], dtype=float)
        name = parts[9]

        R = qvec_to_rotmat(qvec)
        center = -R.T @ tvec
        R_wc = R.T

        images[img_id] = {
            "name": name,
            "center": center,
            "R_wc": R_wc,
            "neighbors": {},
        }
        i += 2  # skip points2D line
    return images


def parse_points3d_txt(path: Path) -> Tuple[np.ndarray, np.ndarray, Dict[int, List[int]]]:
    points = []
    colors = []
    tracks: Dict[int, List[int]] = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        X, Y, Z = map(float, parts[1:4])
        R_, G_, B_ = map(int, parts[4:7])
        points.append([X, Y, Z])
        colors.append([R_, G_, B_])
        track = parts[8:]
        seen_by = [int(track[k]) for k in range(0, len(track), 2)]
        for m in range(len(seen_by)):
            for n in range(m + 1, len(seen_by)):
                a, b = seen_by[m], seen_by[n]
                tracks.setdefault(a, []).append(len(points) - 1)
                tracks.setdefault(b, []).append(len(points) - 1)
    return np.array(points, dtype=float), np.array(colors, dtype=int), tracks


def compute_covisibility(tracks: Dict[int, List[int]], min_shared: int = 20, top_k: int = 5) -> Dict[int, List[int]]:
    counts: Dict[Tuple[int, int], int] = {}
    for cam_id, pts in tracks.items():
        set_pts = set(pts)
        for other_id, other_pts in tracks.items():
            if other_id <= cam_id:
                continue
            shared = len(set_pts.intersection(other_pts))
            if shared >= min_shared:
                counts[(cam_id, other_id)] = shared
    neighbors: Dict[int, List[int]] = {}
    for (a, b), cnt in counts.items():
        neighbors.setdefault(a, []).append((b, cnt))
        neighbors.setdefault(b, []).append((a, cnt))
    pruned = {}
    for cam_id, adj in neighbors.items():
        adj_sorted = sorted(adj, key=lambda x: x[1], reverse=True)
        pruned[cam_id] = [nid for nid, _ in adj_sorted[:top_k]]
    return pruned


def save_ply(points: np.ndarray, colors: np.ndarray, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {len(points)}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("end_header\n")
        for p, c in zip(points, colors):
            f.write(f"{p[0]:.6f} {p[1]:.6f} {p[2]:.6f} {int(c[0])} {int(c[1])} {int(c[2])}\n")


def convert_colmap(
    input_dir: Path = INPUT_DIR,
    image_dir: Path = IMAGE_DIR,
    output_dir: Path = OUTPUT_DIR,
    min_shared: int = 20,
    top_k: int = 5,
) -> Path:
    cameras_txt = input_dir / "cameras.txt"
    images_txt = input_dir / "images.txt"
    points_txt = input_dir / "points3D.txt"

    images_data = parse_images_txt(images_txt)
    points, colors, tracks = parse_points3d_txt(points_txt)
    covis = compute_covisibility(tracks, min_shared=min_shared, top_k=top_k)

    flip = np.diag([1, -1, -1])

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "images").mkdir(parents=True, exist_ok=True)

    # Flip point cloud to Three.js coords (y up, z back)
    points_flipped = (points @ flip.T)
    ply_path = output_dir / "model.ply"
    save_ply(points_flipped, colors, ply_path)

    sorted_ids = sorted(images_data.keys())
    id_map = {old_id: idx for idx, old_id in enumerate(sorted_ids)}

    cameras_export = []
    for old_id in sorted_ids:
        entry = images_data[old_id]
        C_cv = entry["center"]
        C_three = flip @ C_cv
        R_three = flip @ entry["R_wc"] @ flip
        quat = Rotation.from_matrix(R_three).as_quat()

        img_name = entry["name"]
        src_img = image_dir / img_name
        if src_img.exists():
            copy2(src_img, output_dir / "images" / src_img.name)

        neighbors = [id_map[nid] for nid in covis.get(old_id, []) if nid in id_map]

        cameras_export.append(
            {
                "id": id_map[old_id],
                "filename": img_name,
                "position": C_three.astype(float).tolist(),
                "quaternion": quat.astype(float).tolist(),
                "neighbors": neighbors,
            }
        )

    payload = {
        "cameras": cameras_export,
        "point_cloud_path": "assets/model.ply",
    }
    out_json = output_dir / "data.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return out_json


if __name__ == "__main__":
    out = convert_colmap()
    print(f"Wrote {out}")
