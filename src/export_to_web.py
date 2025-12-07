"""Export SfM results to a Three.js-friendly JSON bundle."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from shutil import copy2
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.spatial.transform import Rotation


@dataclass
class CameraExport:
    id: int
    filename: Optional[str]
    position: List[float]  # camera center in world coords (Three.js convention)
    quaternion: List[float]  # [x, y, z, w]
    neighbors: List[int]


def _camera_center(R_wc: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Compute camera center C = -R^T t from world-to-camera pose."""
    return -R_wc.T @ t.reshape(3)


def _flip_cv_to_three(vec: np.ndarray) -> np.ndarray:
    """Flip Y/Z axes to go from OpenCV (y down, z forward) to Three.js (y up, z back)."""
    flip = np.diag([1, -1, -1])
    return flip @ vec


def _rot_cv_to_three_world(R_wc: np.ndarray) -> np.ndarray:
    """
    Convert OpenCV world-to-camera rotation to Three.js world rotation matrix.

    R_wc maps world -> camera. The camera object in Three.js uses the inverse
    (world) rotation. We also flip Y/Z to match coordinate conventions.
    """
    flip = np.diag([1, -1, -1])
    R_world = R_wc.T  # camera orientation in world coords
    return flip @ R_world


def _compute_covisibility(mapper, min_shared: int = 30, top_k: int = 5) -> Dict[int, List[int]]:
    """Build covisibility graph: connect cameras sharing at least min_shared points."""
    counts: Dict[Tuple[int, int], int] = {}
    for track in mapper.tracks.values():
        cams = sorted(track.observations.keys())
        for i in range(len(cams)):
            for j in range(i + 1, len(cams)):
                a, b = cams[i], cams[j]
                key = (a, b) if a < b else (b, a)
                counts[key] = counts.get(key, 0) + 1

    neighbors: Dict[int, List[int]] = {cam_id: [] for cam_id in mapper.cameras}
    for (a, b), cnt in counts.items():
        if cnt >= min_shared:
            neighbors[a].append((b, cnt))
            neighbors[b].append((a, cnt))

    # keep top_k by shared count
    pruned: Dict[int, List[int]] = {}
    for cam_id, adj in neighbors.items():
        adj_sorted = sorted(adj, key=lambda x: x[1], reverse=True)
        pruned[cam_id] = [nid for nid, _ in adj_sorted[:top_k]]
    return pruned


def export_to_web(
    mapper,
    image_paths: Dict[int, str],
    ply_path: str,
    output_dir: str = "viewer/assets",
    min_shared: int = 30,
    top_k: int = 5,
) -> Path:
    """
    Export cameras + covisibility graph to JSON and copy assets for the viewer.

    Args:
        mapper: IncrementalMapper with cameras and tracks.
        image_paths: Mapping camera_id -> source image path.
        ply_path: Path to the point cloud to copy alongside JSON.
        output_dir: Destination directory for data.json, model.ply, images/.
        min_shared: Minimum shared points to connect cameras.
        top_k: Keep top_k neighbors by shared count.
    """
    out_root = Path(output_dir)
    images_dir = out_root / "images"
    out_root.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    # copy ply
    ply_src = Path(ply_path)
    ply_dst = out_root / "model.ply"
    if ply_src.exists():
        copy2(ply_src, ply_dst)

    covis = _compute_covisibility(mapper, min_shared=min_shared, top_k=top_k)

    cameras_export: List[CameraExport] = []
    for cam_id in sorted(mapper.cameras):
        cam = mapper.cameras[cam_id]
        R_wc = cam.R
        t = cam.t
        C_cv = _camera_center(R_wc, t)
        C_three = _flip_cv_to_three(C_cv)
        R_three_world = _rot_cv_to_three_world(R_wc)
        quat = Rotation.from_matrix(R_three_world).as_quat()  # x, y, z, w

        img_name = None
        if cam_id in image_paths:
            src_img = Path(image_paths[cam_id])
            if src_img.exists():
                img_name = src_img.name
                copy2(src_img, images_dir / img_name)

        cameras_export.append(
            CameraExport(
                id=cam_id,
                filename=img_name,
                position=C_three.astype(float).tolist(),
                quaternion=quat.astype(float).tolist(),
                neighbors=covis.get(cam_id, []),
            )
        )

    payload = {
        "cameras": [asdict(c) for c in cameras_export],
        "point_cloud_path": "assets/model.ply",
    }
    out_json = out_root / "data.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return out_json
