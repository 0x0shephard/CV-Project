"""Export COLMAP-style reconstruction (cameras.txt, images.txt, points3D.txt) to viewer bundle."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from shutil import copy2
from typing import Dict, List, Tuple

import numpy as np
from scipy.spatial.transform import Rotation


@dataclass
class CameraExport:
    id: int
    filename: str
    position: List[float]  # Three.js convention (Y up, Z back)
    quaternion: List[float]  # [x, y, z, w]
    neighbors: List[int]


def qvec_to_rotmat(qvec: np.ndarray) -> np.ndarray:
    """Convert COLMAP quaternion (w, x, y, z) to rotation matrix."""
    w, x, y, z = qvec
    return np.array([
        [1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * z * w, 2 * x * z + 2 * y * w],
        [2 * x * y + 2 * z * w, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * x * w],
        [2 * x * z - 2 * y * w, 2 * y * z + 2 * x * w, 1 - 2 * x * x - 2 * y * y],
    ])


def parse_images_txt(path: Path) -> Dict[int, dict]:
    images = {}
    lines = path.read_text().splitlines()
    for i in range(len(lines)):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            continue
        tokens = line.split()
        if len(tokens) < 9:
            continue
        image_id = int(tokens[0])
        qw, qx, qy, qz = map(float, tokens[1:5])
        tx, ty, tz = map(float, tokens[5:8])
        cam_id = int(tokens[8])
        name = tokens[9]
        images[image_id] = {
            "qvec": np.array([qw, qx, qy, qz], dtype=float),
            "tvec": np.array([tx, ty, tz], dtype=float),
            "cam_id": cam_id,
            "name": name,
        }
    return images


def parse_points3d_txt(path: Path) -> Tuple[np.ndarray, np.ndarray, Dict[int, List[int]]]:
    points = []
    colors = []
    tracks: Dict[int, List[int]] = {}
    lines = path.read_text().splitlines()
    for line in lines:
        if not line or line.startswith("#"):
            continue
        tokens = line.split()
        if len(tokens) < 8:
            continue
        X, Y, Z = map(float, tokens[1:4])
        R, G, B = map(int, tokens[4:7])
        points.append([X, Y, Z])
        colors.append([R, G, B])
        # track: remaining tokens after error term; pairs of (image_id, point2d_idx)
        track_tokens = tokens[8:]
        for i in range(0, len(track_tokens), 2):
            try:
                img_id = int(track_tokens[i])
            except ValueError:
                continue
            tracks.setdefault(img_id, []).append(len(points) - 1)
    return np.array(points, dtype=float), np.array(colors, dtype=int), tracks


def compute_covisibility(tracks: Dict[int, List[int]], min_shared: int = 20, top_k: int = 5) -> Dict[int, List[int]]:
    counts: Dict[Tuple[int, int], int] = {}
    for cams, _ in tracks.items():
        pass  # placeholder for type hints
    for cam_id, pts in tracks.items():
        pts_set = set(pts)
        for other_id, other_pts in tracks.items():
            if other_id <= cam_id:
                continue
            shared = len(pts_set.intersection(other_pts))
            if shared >= min_shared:
                key = (cam_id, other_id)
                counts[key] = shared
    neighbors: Dict[int, List[int]] = {}
    all_cam_ids = set([cid for pair in counts for cid in pair])
    for cam_id in all_cam_ids:
        neighbors[cam_id] = []
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


def export_from_colmap(
    images_dir: str,
    cameras_txt: str,
    images_txt: str,
    points3d_txt: str,
    output_dir: str = "viewer/assets",
    min_shared: int = 20,
    top_k: int = 5,
) -> Path:
    """
    Export COLMAP reconstruction to viewer bundle (data.json, model.ply, copied images).
    """
    images_dir = Path(images_dir)
    cameras_path = Path(cameras_txt)
    images_path = Path(images_txt)
    points_path = Path(points3d_txt)
    out_root = Path(output_dir)
    images_out = out_root / "images"
    out_root.mkdir(parents=True, exist_ok=True)
    images_out.mkdir(parents=True, exist_ok=True)

    # Parse COLMAP text files
    images_data = parse_images_txt(images_path)
    points, colors, tracks = parse_points3d_txt(points_path)

    # Covisibility
    covis = compute_covisibility(tracks, min_shared=min_shared, top_k=top_k)

    flip = np.diag([1, -1, -1])
    cameras_export: List[CameraExport] = []
    for img_id, entry in images_data.items():
        qvec = entry["qvec"]
        tvec = entry["tvec"]
        R_wc = qvec_to_rotmat(qvec)
        C_cv = -R_wc.T @ tvec.reshape(3)
        C_three = flip @ C_cv
        R_three_world = flip @ R_wc.T
        quat = Rotation.from_matrix(R_three_world).as_quat()

        img_name = entry["name"]
        src_img = images_dir / img_name
        if src_img.exists():
            copy2(src_img, images_out / src_img.name)

        cameras_export.append(
            CameraExport(
                id=img_id,
                filename=img_name,
                position=C_three.astype(float).tolist(),
                quaternion=quat.astype(float).tolist(),
                neighbors=covis.get(img_id, []),
            )
        )

    # Save PLY (points in COLMAP coords; viewer flips via pointCloud rotation)
    ply_out = out_root / "model.ply"
    save_ply(points, colors, ply_out)

    payload = {
        "cameras": [asdict(c) for c in cameras_export],
        "point_cloud_path": "assets/model.ply",
    }
    out_json = out_root / "data.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return out_json
