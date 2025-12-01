"""Two-view geometry utilities for SfM reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np


@dataclass
class FeatureSet:
    """Container for keypoints and descriptors."""
    keypoints: list[cv2.KeyPoint]
    descriptors: np.ndarray


@dataclass
class MatchResult:
    """Container for feature matching results."""
    matches: list[cv2.DMatch]
    idx1: np.ndarray  # indices into keypoints1
    idx2: np.ndarray  # indices into keypoints2
    pts1: np.ndarray  # 2D points from image 1
    pts2: np.ndarray  # 2D points from image 2


@dataclass
class TwoViewReconstruction:
    """Two-view reconstruction result."""
    R: np.ndarray  # 3x3 rotation matrix
    t: np.ndarray  # 3x1 translation vector
    points3d: np.ndarray  # Nx3 3D points
    match_indices: np.ndarray  # Indices of matches used


def build_projection_matrix(R: np.ndarray, t: np.ndarray, K: np.ndarray) -> np.ndarray:
    """
    Build 3x4 projection matrix P = K[R|t].

    Args:
        R: 3x3 rotation matrix
        t: 3x1 or (3,) translation vector
        K: 3x3 intrinsic matrix

    Returns:
        3x4 projection matrix
    """
    if t.ndim == 1:
        t = t.reshape(3, 1)
    return K @ np.hstack([R, t])


def triangulate_points(pts1: np.ndarray, pts2: np.ndarray, P1: np.ndarray, P2: np.ndarray) -> np.ndarray:
    """
    Triangulate 3D points from two views.

    Args:
        pts1: Nx2 points in image 1
        pts2: Nx2 points in image 2
        P1: 3x4 projection matrix for camera 1
        P2: 3x4 projection matrix for camera 2

    Returns:
        Nx3 array of 3D points
    """
    points_4d = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
    points_3d = (points_4d[:3] / points_4d[3]).T
    return points_3d


def reconstruct_two_views(
    pts1: np.ndarray,
    pts2: np.ndarray,
    K: np.ndarray,
    match_indices: np.ndarray | None = None
) -> TwoViewReconstruction:
    """
    Reconstruct two views using essential matrix.

    Args:
        pts1: Nx2 points in image 1
        pts2: Nx2 points in image 2
        K: 3x3 intrinsic matrix
        match_indices: Optional indices of matches

    Returns:
        TwoViewReconstruction object
    """
    # Estimate essential matrix
    E, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, prob=0.999, threshold=1.0)
    inlier_mask = mask.ravel().astype(bool)

    pts1_inliers = pts1[inlier_mask]
    pts2_inliers = pts2[inlier_mask]

    if match_indices is not None:
        match_indices = match_indices[inlier_mask]

    # Recover pose
    _, R, t, pose_mask = cv2.recoverPose(E, pts1_inliers, pts2_inliers, K)
    pose_mask = pose_mask.ravel().astype(bool)

    pts1_final = pts1_inliers[pose_mask]
    pts2_final = pts2_inliers[pose_mask]

    if match_indices is not None:
        match_indices = match_indices[pose_mask]
    else:
        # Create sequential indices
        match_indices = np.arange(len(pts1_final))

    # Triangulate
    P1 = build_projection_matrix(np.eye(3), np.zeros(3), K)
    P2 = build_projection_matrix(R, t.ravel(), K)
    points_3d = triangulate_points(pts1_final, pts2_final, P1, P2)

    # Filter by cheirality (depth > 0 in both cameras)
    R1 = np.eye(3)
    t1 = np.zeros(3)
    valid_mask = np.ones(len(points_3d), dtype=bool)

    # Check finite and reasonable magnitude (filter extreme values before operations)
    with np.errstate(invalid='ignore', divide='ignore', over='ignore'):
        finite_mask = np.all(np.isfinite(points_3d), axis=1)
        magnitude_mask = np.linalg.norm(points_3d, axis=1) < 1000  # Filter extremely distant points
        valid_mask &= finite_mask & magnitude_mask

        # Only process valid points
        if np.any(valid_mask):
            points_3d_finite = points_3d[valid_mask]

            # Check depth in camera 1
            points_cam1 = (R1 @ points_3d_finite.T).T + t1
            depth_mask1 = points_cam1[:, 2] > 0

            # Update valid_mask
            valid_indices = np.where(valid_mask)[0]
            valid_mask[valid_indices[~depth_mask1]] = False

        if np.any(valid_mask):
            points_3d_finite = points_3d[valid_mask]

            # Check depth in camera 2
            points_cam2 = (R @ points_3d_finite.T).T + t.ravel()
            depth_mask2 = points_cam2[:, 2] > 0

            # Update valid_mask
            valid_indices = np.where(valid_mask)[0]
            valid_mask[valid_indices[~depth_mask2]] = False

    # Filter
    points_3d_final = points_3d[valid_mask]
    match_indices_final = match_indices[valid_mask]

    return TwoViewReconstruction(
        R=R,
        t=t,
        points3d=points_3d_final,
        match_indices=match_indices_final
    )
