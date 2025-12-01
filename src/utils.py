"""Utility functions for I/O and visualization."""

from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .incremental_sfm import IncrementalMapper


def save_point_cloud_ply(points: np.ndarray, colors: np.ndarray, output_path: str, verbose: bool = False):
    """
    Save point cloud to PLY format.

    Args:
        points: Nx3 array of 3D points
        colors: Nx3 array of RGB colors (0-255 or 0-1 float)
        output_path: Path to save PLY file
        verbose: Print progress messages
    """
    if verbose:
        print(f"Saving {len(points)} points to {output_path}...")
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Convert colors to 0-255 range if needed
    if colors.dtype == np.float32 or colors.dtype == np.float64:
        if colors.max() <= 1.0:
            colors = (colors * 255).astype(np.uint8)
        else:
            colors = colors.astype(np.uint8)

    # Build all lines as a list first (much faster than individual writes)
    lines = [
        "ply\n",
        "format ascii 1.0\n",
        f"element vertex {len(points)}\n",
        "property float x\n",
        "property float y\n",
        "property float z\n",
        "property uchar red\n",
        "property uchar green\n",
        "property uchar blue\n",
        "end_header\n"
    ]
    
    # Pre-format all vertex lines
    for point, color in zip(points, colors):
        lines.append(f"{point[0]:.6f} {point[1]:.6f} {point[2]:.6f} "
                    f"{int(color[0])} {int(color[1])} {int(color[2])}\n")
    
    # Write everything at once
    with open(output_path, 'w') as f:
        f.writelines(lines)
    
    if verbose:
        print(f"✓ Saved successfully")


def save_point_cloud_ply_binary(points: np.ndarray, colors: np.ndarray, output_path: str, verbose: bool = False):
    """
    Save point cloud to PLY format in binary mode (much faster for large clouds).

    Args:
        points: Nx3 array of 3D points
        colors: Nx3 array of RGB colors (0-255 or 0-1 float)
        output_path: Path to save PLY file
        verbose: Print progress messages
    """
    import struct
    
    if verbose:
        print(f"Saving {len(points)} points to {output_path} (binary)...")
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Convert colors to 0-255 range if needed
    if colors.dtype == np.float32 or colors.dtype == np.float64:
        if colors.max() <= 1.0:
            colors = (colors * 255).astype(np.uint8)
        else:
            colors = colors.astype(np.uint8)

    # Write header
    header = (
        "ply\n"
        "format binary_little_endian 1.0\n"
        f"element vertex {len(points)}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "property uchar red\n"
        "property uchar green\n"
        "property uchar blue\n"
        "end_header\n"
    )
    
    with open(output_path, 'wb') as f:
        # Write ASCII header
        f.write(header.encode('ascii'))
        
        # Write binary data
        for point, color in zip(points, colors):
            # Pack as: 3 floats (x,y,z) + 3 unsigned chars (r,g,b)
            f.write(struct.pack('fffBBB', 
                              point[0], point[1], point[2],
                              int(color[0]), int(color[1]), int(color[2])))
    
    if verbose:
        print(f"✓ Saved successfully (binary format)")


def export_mapper_to_ply(mapper: IncrementalMapper, output_path: str):
    """
    Export IncrementalMapper point cloud to PLY file.

    Args:
        mapper: IncrementalMapper object
        output_path: Path to save PLY file
    """
    points, colors = mapper.export_points()
    save_point_cloud_ply(points, colors, output_path)


def compute_reprojection_error(points_3d: np.ndarray, points_2d: np.ndarray,
                                K: np.ndarray, R: np.ndarray, t: np.ndarray) -> float:
    """
    Compute mean reprojection error.

    Args:
        points_3d: Nx3 3D points
        points_2d: Nx2 observed 2D points
        K: 3x3 intrinsic matrix
        R: 3x3 rotation matrix
        t: 3x1 translation vector

    Returns:
        Mean reprojection error in pixels
    """
    # Project 3D points
    points_cam = (R @ points_3d.T).T + t.ravel()
    points_proj = (K @ points_cam.T).T
    points_2d_proj = points_proj[:, :2] / points_proj[:, 2:3]

    # Compute errors
    errors = np.linalg.norm(points_2d - points_2d_proj, axis=1)
    return np.mean(errors)


def get_point_cloud_stats(points: np.ndarray) -> dict:
    """
    Get statistics about point cloud.

    Args:
        points: Nx3 array of 3D points

    Returns:
        Dictionary with statistics
    """
    if len(points) == 0:
        return {
            'count': 0,
            'mean': np.zeros(3),
            'std': np.zeros(3),
            'min': np.zeros(3),
            'max': np.zeros(3),
            'range': np.zeros(3)
        }

    return {
        'count': len(points),
        'mean': np.mean(points, axis=0),
        'std': np.std(points, axis=0),
        'min': np.min(points, axis=0),
        'max': np.max(points, axis=0),
        'range': np.ptp(points, axis=0)
    }
