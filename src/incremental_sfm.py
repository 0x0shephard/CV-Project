"""Incremental Structure-from-Motion utilities for multi-view reconstruction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import cv2
import numpy as np

from . import feature_matching
from .two_view_geometry import build_projection_matrix, triangulate_points


@dataclass
class CameraPose:
    image_idx: int
    R: np.ndarray
    t: np.ndarray

    def projection_matrix(self, K: np.ndarray) -> np.ndarray:
        return build_projection_matrix(self.R, self.t, K)


@dataclass
class MapPoint:
    id: int
    coord: np.ndarray
    color: np.ndarray
    observations: Dict[int, int] = field(default_factory=dict)


@dataclass
class ImageFeatures:
    feature_set: feature_matching.FeatureSet
    image: np.ndarray

    @property
    def keypoints(self) -> List[cv2.KeyPoint]:
        return self.feature_set.keypoints

    @property
    def descriptors(self) -> np.ndarray:
        return self.feature_set.descriptors


def _sample_color(image: np.ndarray, pt: Tuple[float, float]) -> np.ndarray:
    h, w = image.shape[:2]
    x = int(round(pt[0]))
    y = int(round(pt[1]))
    x = max(0, min(w - 1, x))
    y = max(0, min(h - 1, y))
    return image[y, x].astype(np.float32)


class IncrementalMapper:
    def __init__(self, K: np.ndarray, min_pnp_points: int = 40) -> None:
        self.K = K
        self.min_pnp_points = min_pnp_points
        self.cameras: Dict[int, CameraPose] = {}
        self.tracks: Dict[int, MapPoint] = {}
        self.kp_track_lookup: Dict[Tuple[int, int], int] = {}
        self.images: Dict[int, ImageFeatures] = {}
        self._next_track_id = 0

    def register_image(self, idx: int, features: ImageFeatures) -> None:
        self.images[idx] = features

    def _add_camera(self, idx: int, R: np.ndarray, t: np.ndarray) -> None:
        self.cameras[idx] = CameraPose(image_idx=idx, R=R, t=t.reshape(3))

    def initialize_from_pair(
        self,
        idx0: int,
        idx1: int,
        reconstruction,
        match_result: feature_matching.MatchResult,
    ) -> None:
        self._add_camera(idx0, np.eye(3), np.zeros(3))
        self._add_camera(idx1, reconstruction.R, reconstruction.t)

        feats0 = self.images[idx0]
        feats1 = self.images[idx1]

        for order, match_idx in enumerate(reconstruction.match_indices):
            kp0_idx = match_result.idx1[match_idx]
            kp1_idx = match_result.idx2[match_idx]
            coord = reconstruction.points3d[order]
            color0 = _sample_color(feats0.image, feats0.keypoints[kp0_idx].pt)
            color1 = _sample_color(feats1.image, feats1.keypoints[kp1_idx].pt)
            color = (color0 + color1) / 2.0
            track_id = self._next_track_id
            self._next_track_id += 1
            self.tracks[track_id] = MapPoint(
                id=track_id,
                coord=coord,
                color=color,
                observations={idx0: kp0_idx, idx1: kp1_idx},
            )
            self.kp_track_lookup[(idx0, kp0_idx)] = track_id
            self.kp_track_lookup[(idx1, kp1_idx)] = track_id

    def _collect_pnp_correspondences(
        self, idx: int
    ) -> Tuple[np.ndarray, np.ndarray, List[int], List[int]]:
        feats_new = self.images[idx]
        pts3d: List[np.ndarray] = []
        pts2d: List[np.ndarray] = []
        track_ids: List[int] = []
        kp_indices: List[int] = []
        for ref_idx, cam in self.cameras.items():
            if ref_idx == idx:
                continue
            match = feature_matching.match_features(
                self.images[ref_idx].feature_set,
                feats_new.feature_set,
            )
            for kp_ref_idx, kp_new_idx, pt_new in zip(match.idx1, match.idx2, match.pts2):
                track_id = self.kp_track_lookup.get((ref_idx, kp_ref_idx))
                if track_id is None:
                    continue
                track = self.tracks[track_id]
                pts3d.append(track.coord)
                pts2d.append(pt_new)
                track_ids.append(track_id)
                kp_indices.append(kp_new_idx)
        if not pts3d:
            return np.empty((0, 3)), np.empty((0, 2)), [], []
        return (
            np.array(pts3d, dtype=np.float32),
            np.array(pts2d, dtype=np.float32),
            track_ids,
            kp_indices,
        )

    def _solve_pnp(self, pts3d: np.ndarray, pts2d: np.ndarray):
        success, rvec, tvec, inliers = cv2.solvePnPRansac(
            pts3d,
            pts2d,
            self.K,
            distCoeffs=None,
            flags=cv2.SOLVEPNP_SQPNP,
            iterationsCount=200,
            reprojectionError=3.0,
            confidence=0.999,
        )
        if not success or inliers is None or len(inliers) < self.min_pnp_points:
            return None
        R, _ = cv2.Rodrigues(rvec)
        return R, tvec.reshape(3), inliers.ravel()

    def register_new_view(self, idx: int) -> bool:
        pts3d, pts2d, track_ids, kp_indices = self._collect_pnp_correspondences(idx)
        if len(track_ids) < self.min_pnp_points:
            return False
        result = self._solve_pnp(pts3d, pts2d)
        if result is None:
            return False
        R, t, inliers = result
        # keep only inlier correspondences
        inlier_ids = [track_ids[i] for i in inliers]
        inlier_kps = [kp_indices[i] for i in inliers]
        self._add_camera(idx, R, t)
        for track_id, kp_idx in zip(inlier_ids, inlier_kps):
            self.tracks[track_id].observations[idx] = kp_idx
            self.kp_track_lookup[(idx, kp_idx)] = track_id

        self._triangulate_new_points(idx)
        return True

    def _triangulate_new_points(self, idx: int) -> None:
        new_cam = self.cameras[idx]
        feats_new = self.images[idx]
        P_new = new_cam.projection_matrix(self.K)
        for ref_idx, cam in self.cameras.items():
            if ref_idx >= idx:
                continue
            feats_ref = self.images[ref_idx]
            match = feature_matching.match_features(
                feats_ref.feature_set, feats_new.feature_set
            )
            if len(match.matches) < 50:
                continue
            pts_ref = []
            pts_new = []
            ref_indices = []
            new_indices = []
            for local_idx, (kp_ref_idx, kp_new_idx) in enumerate(zip(match.idx1, match.idx2)):
                if (ref_idx, kp_ref_idx) in self.kp_track_lookup:
                    continue
                pts_ref.append(match.pts1[local_idx])
                pts_new.append(match.pts2[local_idx])
                ref_indices.append(kp_ref_idx)
                new_indices.append(kp_new_idx)
            if not pts_ref:
                continue
            P_ref = cam.projection_matrix(self.K)
            pts_ref_np = np.array(pts_ref, dtype=np.float32)
            pts_new_np = np.array(pts_new, dtype=np.float32)
            points3d = triangulate_points(pts_ref_np, pts_new_np, P_ref, P_new)

            # Filter for finite and reasonable magnitude values
            with np.errstate(invalid='ignore', divide='ignore', over='ignore'):
                finite_mask = np.all(np.isfinite(points3d), axis=1)
                magnitude_mask = np.linalg.norm(points3d, axis=1) < 1000
                valid_mask = finite_mask & magnitude_mask

                if not valid_mask.any():
                    continue

                # Only operate on valid points
                points3d_valid = points3d[valid_mask]

                # depth filtering
                points_cam_new = (new_cam.R @ points3d_valid.T + new_cam.t.reshape(3, 1)).T
                depth_mask = points_cam_new[:, 2] > 0

                # Map back to full mask
                mask = np.zeros(len(points3d), dtype=bool)
                valid_indices = np.where(valid_mask)[0]
                mask[valid_indices[depth_mask]] = True
            for coord, ref_kp_idx, new_kp_idx, valid in zip(
                points3d, ref_indices, new_indices, mask
            ):
                if not valid:
                    continue
                color_new = _sample_color(feats_new.image, feats_new.keypoints[new_kp_idx].pt)
                color_ref = _sample_color(feats_ref.image, feats_ref.keypoints[ref_kp_idx].pt)
                color = (color_new + color_ref) / 2.0
                track_id = self._next_track_id
                self._next_track_id += 1
                mp = MapPoint(
                    id=track_id,
                    coord=coord,
                    color=color,
                    observations={ref_idx: ref_kp_idx, idx: new_kp_idx},
                )
                self.tracks[track_id] = mp
                self.kp_track_lookup[(ref_idx, ref_kp_idx)] = track_id
                self.kp_track_lookup[(idx, new_kp_idx)] = track_id

    def export_points(self) -> Tuple[np.ndarray, np.ndarray]:
        if not self.tracks:
            return np.empty((0, 3)), np.empty((0, 3))
        coords = np.array([mp.coord for mp in self.tracks.values()], dtype=np.float32)
        colors = np.array([mp.color for mp in self.tracks.values()], dtype=np.float32)
        return coords, colors

    def build_observation_matrices(self):
        camera_indices = []
        point_indices = []
        points_2d = []
        camera_id_to_idx = {cam_id: i for i, cam_id in enumerate(sorted(self.cameras))}
        track_id_to_idx = {track_id: i for i, track_id in enumerate(sorted(self.tracks))}
        for track_id, track in self.tracks.items():
            for img_idx, kp_idx in track.observations.items():
                if img_idx not in self.cameras:
                    continue
                camera_indices.append(camera_id_to_idx[img_idx])
                point_indices.append(track_id_to_idx[track_id])
                kp = self.images[img_idx].keypoints[kp_idx]
                points_2d.append(kp.pt)
        return (
            np.array(camera_indices),
            np.array(point_indices),
            np.array(points_2d, dtype=np.float32),
            camera_id_to_idx,
            track_id_to_idx,
        )
