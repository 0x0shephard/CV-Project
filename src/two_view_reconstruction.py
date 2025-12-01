"""Two-view geometry: Essential matrix, pose recovery, and triangulation."""

import cv2
import numpy as np
from typing import Tuple, Optional


def estimate_essential_matrix(pts1: np.ndarray, pts2: np.ndarray, K: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Estimate essential matrix using RANSAC.

    Args:
        pts1: Nx2 points in image 1
        pts2: Nx2 points in image 2
        K: 3x3 intrinsic matrix

    Returns:
        Tuple of (essential_matrix, inlier_mask)
    """
    E, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, prob=0.999, threshold=1.0)
    return E, mask.ravel().astype(bool)


def recover_pose_from_essential(E: np.ndarray, pts1: np.ndarray, pts2: np.ndarray, K: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Recover relative pose (R, t) from essential matrix.

    Args:
        E: 3x3 essential matrix
        pts1: Nx2 inlier points in image 1
        pts2: Nx2 inlier points in image 2
        K: 3x3 intrinsic matrix

    Returns:
        Tuple of (R, t, pose_mask) where R is 3x3 rotation, t is 3x1 translation
    """
    _, R, t, pose_mask = cv2.recoverPose(E, pts1, pts2, K)
    return R, t, pose_mask.ravel().astype(bool)


def triangulate_points(P1: np.ndarray, P2: np.ndarray, pts1: np.ndarray, pts2: np.ndarray) -> np.ndarray:
    """
    Triangulate 3D points from two views.

    Args:
        P1: 3x4 projection matrix for camera 1
        P2: 3x4 projection matrix for camera 2
        pts1: Nx2 points in image 1
        pts2: Nx2 points in image 2

    Returns:
        Nx3 array of 3D points
    """
    points_4d = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
    points_3d = (points_4d[:3] / points_4d[3]).T
    return points_3d


def filter_points_by_cheirality(points_3d: np.ndarray, R1: np.ndarray, t1: np.ndarray,
                                 R2: np.ndarray, t2: np.ndarray) -> np.ndarray:
    """
    Filter 3D points to keep only those in front of both cameras.

    Args:
        points_3d: Nx3 array of 3D points
        R1, t1: Rotation and translation of camera 1
        R2, t2: Rotation and translation of camera 2

    Returns:
        Boolean mask of valid points
    """
    valid_mask = np.ones(len(points_3d), dtype=bool)

    # Check for finite values
    finite_mask = np.all(np.isfinite(points_3d), axis=1)
    valid_mask &= finite_mask

    if not np.any(valid_mask):
        return valid_mask

    # Transform points to camera 1 frame
    points_cam1 = (R1 @ points_3d[valid_mask].T).T + t1.ravel()
    depth_mask1 = points_cam1[:, 2] > 0

    # Update mask
    valid_indices = np.where(valid_mask)[0]
    valid_mask[valid_indices[~depth_mask1]] = False

    if not np.any(valid_mask):
        return valid_mask

    # Transform points to camera 2 frame
    points_cam2 = (R2 @ points_3d[valid_mask].T).T + t2.ravel()
    depth_mask2 = points_cam2[:, 2] > 0

    # Update mask again
    valid_indices = np.where(valid_mask)[0]
    valid_mask[valid_indices[~depth_mask2]] = False

    return valid_mask
