"""Bundle Adjustment for global refinement of cameras and 3D points."""

from __future__ import annotations

import cv2
import numpy as np
from scipy.optimize import least_squares
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .incremental_sfm import IncrementalMapper


def project_points(points_3d: np.ndarray, K: np.ndarray, R: np.ndarray, t: np.ndarray) -> np.ndarray:
    """
    Project 3D points to 2D using camera parameters.

    Args:
        points_3d: Nx3 3D points
        K: 3x3 intrinsic matrix
        R: 3x3 rotation matrix
        t: 3x1 translation vector

    Returns:
        Nx2 projected 2D points
    """
    # Transform to camera coordinates
    points_cam = (R @ points_3d.T).T + t.ravel()

    # Project to image plane
    points_proj = (K @ points_cam.T).T
    points_2d = points_proj[:, :2] / points_proj[:, 2:3]

    return points_2d


def bundle_adjustment_residuals(params: np.ndarray,
                                 n_cameras: int,
                                 n_points: int,
                                 camera_indices: np.ndarray,
                                 point_indices: np.ndarray,
                                 points_2d: np.ndarray,
                                 K: np.ndarray) -> np.ndarray:
    """
    Compute reprojection residuals for bundle adjustment.

    Args:
        params: Flattened parameter vector [camera_params, point_params]
               Each camera: 6 params (3 for rotation as axis-angle, 3 for translation)
               Each point: 3 params (x, y, z)
        n_cameras: Number of cameras
        n_points: Number of 3D points
        camera_indices: Camera index for each observation
        point_indices: Point index for each observation
        points_2d: Observed 2D points (Nx2)
        K: Intrinsic matrix

    Returns:
        Residual vector (2*N_observations,)
    """
    camera_params = params[:n_cameras * 6].reshape((n_cameras, 6))
    points_3d = params[n_cameras * 6:].reshape((n_points, 3))

    residuals = []

    for i in range(len(camera_indices)):
        cam_idx = camera_indices[i]
        pt_idx = point_indices[i]
        observed = points_2d[i]

        # Get camera parameters
        rvec = camera_params[cam_idx, :3]
        tvec = camera_params[cam_idx, 3:6]

        # Convert rotation vector to matrix
        R, _ = cv2.Rodrigues(rvec)
        t = tvec.reshape(3, 1)

        # Project point
        point_3d = points_3d[pt_idx]
        projected = project_points(point_3d.reshape(1, 3), K, R, t)[0]

        # Compute residual
        residual = observed - projected
        residuals.append(residual)

    return np.concatenate(residuals)


# def run_bundle_adjustment(mapper: IncrementalMapper, max_iterations: int = 50, verbose: bool = False) -> tuple[float, float]:
#     """
#     Run bundle adjustment to refine cameras and 3D points.

#     Args:
#         mapper: IncrementalMapper object with cameras and tracks
#         max_iterations: Maximum optimization iterations (default: 50)
#         verbose: If True, print optimization progress (default: False)

#     Returns:
#         Tuple of (initial_rmse, final_rmse)
#     """
#     # Get observation data
#     camera_indices, point_indices, points_2d, camera_id_map, track_id_map = mapper.build_observation_matrices()

#     if len(camera_indices) == 0:
#         print("Warning: No observations found for bundle adjustment")
#         return 0.0, 0.0

#     n_cameras = len(mapper.cameras)
#     n_points = len(mapper.tracks)
#     n_observations = len(camera_indices)

#     if verbose:
#         print(f"Bundle Adjustment setup:")
#         print(f"  Cameras: {n_cameras}")
#         print(f"  3D Points: {n_points}")
#         print(f"  Observations: {n_observations}")
#         print(f"  Parameters: {n_cameras * 6 + n_points * 3}")

#     # Build initial parameter vector
#     camera_list = sorted(mapper.cameras.keys())
#     track_list = sorted(mapper.tracks.keys())

#     camera_params = []
#     for cam_id in camera_list:
#         cam = mapper.cameras[cam_id]
#         rvec, _ = cv2.Rodrigues(cam.R)
#         camera_params.extend(rvec.ravel())
#         camera_params.extend(cam.t.ravel())

#     point_params = []
#     for track_id in track_list:
#         track = mapper.tracks[track_id]
#         point_params.extend(track.coord)

#     params = np.array(camera_params + point_params, dtype=np.float64)

#     # Compute initial RMSE
#     residuals_init = bundle_adjustment_residuals(
#         params, n_cameras, n_points,
#         camera_indices, point_indices, points_2d, mapper.K
#     )
#     initial_rmse = np.sqrt(np.mean(residuals_init ** 2))

#     if verbose:
#         print(f"  Initial RMSE: {initial_rmse:.3f} pixels")

#     # Run optimization with better termination criteria
#     result = least_squares(
#         bundle_adjustment_residuals,
#         params,
#         args=(n_cameras, n_points, camera_indices, point_indices, points_2d, mapper.K),
#         max_nfev=max_iterations,
#         ftol=1e-4,  # More lenient tolerance for faster convergence
#         xtol=1e-4,  # More lenient parameter tolerance
#         verbose=2 if verbose else 0,  # Show progress if verbose
#         method='trf'  # Trust Region Reflective algorithm
#     )

#     if verbose:
#         print(f"  Optimization status: {result.status}")
#         print(f"  Iterations: {result.nfev}")
#         print(f"  Success: {result.success}")

#     # Extract refined parameters
#     refined_params = result.x
#     camera_params_refined = refined_params[:n_cameras * 6].reshape((n_cameras, 6))
#     points_refined = refined_params[n_cameras * 6:].reshape((n_points, 3))

#     # Update mapper with refined values
#     for i, cam_id in enumerate(camera_list):
#         rvec = camera_params_refined[i, :3]
#         tvec = camera_params_refined[i, 3:6]
#         R, _ = cv2.Rodrigues(rvec)
#         mapper.cameras[cam_id].R = R
#         mapper.cameras[cam_id].t = tvec

#     for i, track_id in enumerate(track_list):
#         mapper.tracks[track_id].coord = points_refined[i]

#     # Compute final RMSE
#     final_rmse = np.sqrt(np.mean(result.fun ** 2))

#     if verbose:
#         print(f"  Final RMSE: {final_rmse:.3f} pixels")

#     return initial_rmse, final_rmse

def run_bundle_adjustment(
    mapper: IncrementalMapper,
    max_iterations: int = 50,
    verbose: bool = False,
    quick_tolerances: bool = False,
    downsample_observations: float | int | None = None,
    random_state: int = 0,
) -> tuple[float, float]:
    # Get observation data
    camera_indices, point_indices, points_2d, camera_id_map, track_id_map = mapper.build_observation_matrices()

    if len(camera_indices) == 0:
        print("Warning: No observations found for bundle adjustment")
        return 0.0, 0.0

    camera_list = sorted(mapper.cameras.keys())
    track_list = sorted(mapper.tracks.keys())

    n_cameras = len(camera_list)
    n_points = len(track_list)
    n_observations = len(camera_indices)

    if downsample_observations is not None:
        obs_count = n_observations
        if isinstance(downsample_observations, float) and downsample_observations < 1.0:
            keep = max(1, int(obs_count * downsample_observations))
        else:
            keep = min(int(downsample_observations), obs_count)
        if keep < obs_count:
            rng = np.random.default_rng(random_state)
            subset = np.sort(rng.choice(obs_count, size=keep, replace=False))
            camera_indices = camera_indices[subset]
            point_indices = point_indices[subset]
            points_2d = points_2d[subset]

            # Re-index points to a compact set and filter track list
            unique_pts = np.unique(point_indices)
            old_to_new = {old: new for new, old in enumerate(unique_pts)}
            point_indices = np.array([old_to_new[i] for i in point_indices], dtype=int)
            track_list = [track_list[i] for i in unique_pts]
            n_points = len(track_list)
            n_observations = keep

            if verbose:
                print(f"Downsampled observations: {keep}/{obs_count} -> {n_points} points")

    if verbose:
        print("Bundle Adjustment setup:")
        print(f"  Cameras: {n_cameras}")
        print(f"  3D Points: {n_points}")
        print(f"  Observations: {n_observations}")
        print(f"  Parameters: {n_cameras * 6 + n_points * 3}")

    # Build initial parameter vector
    camera_params = []
    for cam_id in camera_list:
        cam = mapper.cameras[cam_id]
        rvec, _ = cv2.Rodrigues(cam.R)
        camera_params.extend(rvec.ravel())
        camera_params.extend(cam.t.ravel())

    point_params = []
    for track_id in track_list:
        track = mapper.tracks[track_id]
        point_params.extend(track.coord)

    params = np.array(camera_params + point_params, dtype=np.float64)

    # Initial RMSE
    residuals_init = bundle_adjustment_residuals(
        params, n_cameras, n_points,
        camera_indices, point_indices, points_2d, mapper.K
    )
    initial_rmse = np.sqrt(np.mean(residuals_init ** 2))

    if verbose:
        print(f"  Initial RMSE: {initial_rmse:.3f} pixels")

    # Solver settings (Option 1: quick tolerances)
    ftol = 1e-2 if quick_tolerances else 1e-4
    xtol = 1e-2 if quick_tolerances else 1e-4

    result = least_squares(
        bundle_adjustment_residuals,
        params,
        args=(n_cameras, n_points, camera_indices, point_indices, points_2d, mapper.K),
        max_nfev=max_iterations,
        ftol=ftol,
        xtol=xtol,
        verbose=2 if verbose else 0,
        method='trf'
    )

    if verbose:
        print(f"  Optimization status: {result.status}")
        print(f"  Iterations: {result.nfev}")
        print(f"  Success: {result.success}")

    refined_params = result.x
    camera_params_refined = refined_params[:n_cameras * 6].reshape((n_cameras, 6))
    points_refined = refined_params[n_cameras * 6:].reshape((n_points, 3))

    # Update mapper (only the cameras and tracks we optimized)
    for i, cam_id in enumerate(camera_list):
        rvec = camera_params_refined[i, :3]
        tvec = camera_params_refined[i, 3:6]
        R, _ = cv2.Rodrigues(rvec)
        mapper.cameras[cam_id].R = R
        mapper.cameras[cam_id].t = tvec

    for i, track_id in enumerate(track_list):
        mapper.tracks[track_id].coord = points_refined[i]

    final_rmse = np.sqrt(np.mean(result.fun ** 2))

    if verbose:
        print(f"  Final RMSE: {final_rmse:.3f} pixels")

    return initial_rmse, final_rmse
