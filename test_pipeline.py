"""Quick test of the Week 3 SfM pipeline."""

import sys
import cv2
import numpy as np
from glob import glob
from pathlib import Path

# Import modules
from src.camera import build_intrinsic_matrix
from src.feature_matching import FeatureMatcher, match_features
from src.two_view_geometry import FeatureSet, reconstruct_two_views
from src.incremental_sfm import IncrementalMapper, ImageFeatures
from src.bundle_adjustment import run_bundle_adjustment
from src.utils import export_mapper_to_ply, get_point_cloud_stats

def main():
    print("Testing Week 3 SfM Pipeline\n" + "="*50)

    # Load images
    DATA_DIR = "Data"
    image_paths = sorted(glob(f"{DATA_DIR}/*.jpeg"))
    print(f"✓ Found {len(image_paths)} images")

    if len(image_paths) < 2:
        print("❌ Need at least 2 images")
        return

    # Load first two images for testing
    img1 = cv2.imread(image_paths[9])
    img2 = cv2.imread(image_paths[10])
    h, w = img1.shape[:2]

    # Build intrinsic matrix
    K = build_intrinsic_matrix(w, h)
    print(f"✓ Built intrinsic matrix (focal length: {K[0,0]:.0f})")

    # Detect features
    print("✓ Detecting features...")
    matcher = FeatureMatcher(detector_type='SIFT')

    kp1, desc1 = matcher.detect_and_compute(img1)
    kp2, desc2 = matcher.detect_and_compute(img2)
    print(f"  Image 1: {len(kp1)} features")
    print(f"  Image 2: {len(kp2)} features")

    # Match features
    feats1 = FeatureSet(keypoints=kp1, descriptors=desc1)
    feats2 = FeatureSet(keypoints=kp2, descriptors=desc2)
    match_result = match_features(feats1, feats2)
    print(f"✓ Matched {len(match_result.matches)} features")

    # Two-view reconstruction
    print("✓ Reconstructing two views...")
    reconstruction = reconstruct_two_views(
        match_result.pts1,
        match_result.pts2,
        K,
        match_indices=np.arange(len(match_result.matches))
    )
    print(f"  Created {len(reconstruction.points3d)} 3D points")

    # Initialize mapper
    print("✓ Initializing IncrementalMapper...")
    mapper = IncrementalMapper(K=K, min_pnp_points=40)

    img_feats1 = ImageFeatures(feature_set=feats1, image=img1)
    img_feats2 = ImageFeatures(feature_set=feats2, image=img2)

    mapper.register_image(0, img_feats1)
    mapper.register_image(1, img_feats2)

    mapper.initialize_from_pair(0, 1, reconstruction, match_result)
    print(f"  Cameras: {len(mapper.cameras)}, Points: {len(mapper.tracks)}")

    # Test bundle adjustment
    print("✓ Testing Bundle Adjustment...")
    initial_rmse, final_rmse = run_bundle_adjustment(mapper, max_iterations=50)
    print(f"  Initial RMSE: {initial_rmse:.3f} pixels")
    print(f"  Final RMSE:   {final_rmse:.3f} pixels")

    # Export point cloud
    output_dir = Path("output/week3")
    output_dir.mkdir(parents=True, exist_ok=True)
    ply_path = output_dir / "test_reconstruction.ply"
    export_mapper_to_ply(mapper, str(ply_path))
    print(f"✓ Exported point cloud to {ply_path}")

    # Print statistics
    points, colors = mapper.export_points()
    stats = get_point_cloud_stats(points)
    print(f"\nPoint Cloud Statistics:")
    print(f"  Count: {stats['count']}")
    print(f"  Mean:  [{stats['mean'][0]:.2f}, {stats['mean'][1]:.2f}, {stats['mean'][2]:.2f}]")
    print(f"  Range: [{stats['range'][0]:.2f}, {stats['range'][1]:.2f}, {stats['range'][2]:.2f}]")

    print("\n" + "="*50)
    print("✓ All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
