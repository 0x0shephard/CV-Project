"""Camera intrinsic matrix construction and utilities."""

import numpy as np


def build_intrinsic_matrix(image_width: int, image_height: int) -> np.ndarray:
    """
    Construct camera intrinsic matrix K using simple assumptions.

    Args:
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        3x3 intrinsic matrix K
    """
    focal_length = max(image_width, image_height)
    cx = image_width / 2.0
    cy = image_height / 2.0

    K = np.array([
        [focal_length, 0, cx],
        [0, focal_length, cy],
        [0, 0, 1]
    ], dtype=np.float64)

    return K
