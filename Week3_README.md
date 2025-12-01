# Week 3: Multi-View Structure from Motion with Bundle Adjustment

## Overview

Week 3 extends the two-view reconstruction from Week 2 to handle multiple views using:
- **Incremental SfM**: Adding views sequentially using PnP (Perspective-n-Point)
- **Bundle Adjustment**: Global refinement to minimize reprojection error across all views

## Project Structure

```
Project/
├── src/                          # Modular Python code (Week 3 requirement)
│   ├── camera.py                 # Camera intrinsic matrix utilities
│   ├── feature_matching.py       # SIFT/ORB detection and Lowe's ratio test
│   ├── two_view_geometry.py      # Essential matrix, pose recovery, triangulation
│   ├── incremental_sfm.py        # PnP-based view addition and point triangulation
│   ├── bundle_adjustment.py      # Global optimization using scipy
│   └── utils.py                  # PLY export and statistics
├── notebooks/
│   ├── week1_demo.ipynb          # Week 1 & 2 implementation
│   └── week3_demo.ipynb          # Week 3 demonstration notebook
├── Data/                         # Input images (.jpeg)
└── output/week3/                 # Output PLY files and visualizations
```

## Implementation Details

### 1. Two-View Initialization (`two_view_geometry.py`)

```python
def reconstruct_two_views(pts1, pts2, K, match_indices=None) -> TwoViewReconstruction
```

- Estimates essential matrix using `cv2.findEssentialMat` with RANSAC
- Recovers relative pose (R, t) using `cv2.recoverPose`
- Triangulates 3D points using `cv2.triangulatePoints`
- Filters points by cheirality (depth > 0 in both cameras)
- Returns initial reconstruction with camera poses and 3D points

### 2. Incremental SfM (`incremental_sfm.py`)

**Classes:**
- `CameraPose`: Camera with rotation R, translation t, and stored features
- `MapPoint`: 3D point with position, color, and observations (which cameras see it)
- `ImageFeatures`: Container for features and original image
- `IncrementalMapper`: Main class managing cameras and 3D points

**Key Method:**
```python
def register_new_view(idx: int) -> bool
```

**PnP Pipeline:**
1. **Match Features**: Match new image against all existing cameras
2. **Find 2D-3D Correspondences**: Link new 2D features to existing 3D points
3. **Solve PnP**: Use `cv2.solvePnPRansac` to estimate camera pose
   - Requires ≥40 inliers (configurable with `min_pnp_points`)
   - Uses RANSAC with 3.0 pixel reprojection threshold
4. **Update Observations**: Add inlier correspondences to 3D points
5. **Triangulate New Points**: Create new 3D points between new view and existing views

### 3. Bundle Adjustment (`bundle_adjustment.py`)

```python
def run_bundle_adjustment(mapper: IncrementalMapper, max_iterations: int = 100) -> tuple[float, float]
```

**Optimization:**
- **Parameters**: Camera poses (6 DOF: rotation as axis-angle + translation) and 3D point positions
- **Cost Function**: Sum of squared reprojection errors across all observations
- **Solver**: `scipy.optimize.least_squares` with Levenberg-Marquardt
- **Output**: (initial_rmse, final_rmse) in pixels

**Before/After Comparison:**
- Before BA: Individual PnP solutions accumulate drift
- After BA: All cameras and points refined jointly, reducing overall error

### 4. Utilities (`utils.py`)

- `save_point_cloud_ply()`: Export 3D points with RGB colors to PLY format
- `export_mapper_to_ply()`: Convenience wrapper for IncrementalMapper
- `get_point_cloud_stats()`: Compute mean, range, and statistics

## Usage

### Running the Notebook

```bash
cd /path/to/Project
jupyter notebook notebooks/week3_demo.ipynb
```

The notebook demonstrates:
1. Feature detection on all images
2. Two-view initialization from best pair (images 9 and 10)
3. Incremental view addition using PnP
4. Bundle adjustment refinement
5. Before/after comparison and PLY export

### Running the Test Script

```bash
python3 test_pipeline.py
```

Output:
```
Testing Week 3 SfM Pipeline
==================================================
✓ Found 22 images
✓ Built intrinsic matrix (focal length: 1280)
✓ Detecting features...
  Image 1: 3402 features
  Image 2: 3062 features
✓ Matched 613 features
✓ Reconstructing two views...
  Created 439 3D points
✓ Initializing IncrementalMapper...
  Cameras: 2, Points: 439
✓ Testing Bundle Adjustment...
  Initial RMSE: 0.237 pixels
  Final RMSE:   0.205 pixels
✓ Exported point cloud to output/week3/test_reconstruction.ply
```

## Key Results

### Reconstruction Quality
- **RMSE**: Final reprojection error < 0.3 pixels (very good)
- **Point Cloud Scale**: Points within 10-20 units from origin (reasonable scale)
- **Cameras Added**: Successfully adds multiple views when sufficient overlap exists

### Dataset Challenges
The provided dataset has:
- Sequential capture (1-second intervals)
- Small baseline between consecutive frames
- Rotation-heavy motion (limited parallax)
- Non-consecutive pairs may lack sufficient overlap

**Impact:** PnP success rate limited by small baselines. Best results from well-spaced image pairs.

**Recommendation:** For better multi-view reconstruction:
- Use every 3rd or 5th image instead of consecutive frames
- Ensure camera motion has significant translation component
- Capture images with intentional parallax

## Technical Details

### Camera Intrinsic Matrix
```python
focal_length = max(image_width, image_height)  # 1280 for 960x1280 images
K = [[fx,  0, cx],
     [ 0, fy, cy],
     [ 0,  0,  1]]
```
where `fx = fy = focal_length`, `cx = width/2`, `cy = height/2`

### PnP RANSAC Parameters
```python
cv2.solvePnPRansac(
    points_3d, points_2d, K, None,
    iterationsCount=200,
    reprojectionError=3.0,
    confidence=0.999,
    flags=cv2.SOLVEPNP_SQPNP  # Fast minimal solver
)
```

### Bundle Adjustment Details
- **Parameterization**: Rotation as axis-angle (3 params), translation (3 params)
- **Observations**: All 2D feature observations of 3D points across all cameras
- **Jacobian**: Sparse structure (each observation depends on 1 camera + 1 point)
- **Convergence**: `ftol=1e-6`, typically converges in 20-50 iterations

## Output Files

### PLY Files
- `output/week3/reconstruction_before_ba.ply`: Before bundle adjustment
- `output/week3/reconstruction_after_ba.ply`: After bundle adjustment

View with:
- MeshLab
- CloudCompare
- Open3D
- Any PLY viewer

### Visualizations
- `output/week3/initialization_matches.png`: Feature matches for initialization pair
- `output/week3/comparison_before_after_ba.png`: 2D plots comparing before/after BA

## Code Quality

- ✓ Modular design with separate concerns
- ✓ Type hints using modern Python syntax
- ✓ Dataclasses for clean data structures
- ✓ Comprehensive docstrings
- ✓ Error handling for edge cases
- ✓ Finite value filtering to avoid NaN/Inf
- ✓ Follows project specification requirements

## Comparison with Week 1 & 2

| Aspect | Week 1 & 2 | Week 3 |
|--------|-----------|---------|
| **Code Structure** | Notebook-only | Modular `.py` files + notebook |
| **Views** | 2 views | Multiple views (2+) |
| **Reconstruction** | Two-view geometry | Incremental SfM with PnP |
| **Refinement** | None | Bundle Adjustment |
| **Scale Consistency** | Single baseline | Multi-view with global optimization |
| **Drift Correction** | N/A | Yes, via Bundle Adjustment |

## References

- Hartley & Zisserman, "Multiple View Geometry in Computer Vision"
- Snavely et al., "Photo Tourism: Exploring Photo Collections in 3D"
- Triggs et al., "Bundle Adjustment - A Modern Synthesis"
- OpenCV documentation: `solvePnPRansac`, `triangulatePoints`

## Dependencies

```
opencv-python>=4.5.0
numpy>=1.20.0
scipy>=1.7.0
matplotlib>=3.3.0
```

## Authors

Implementation for Computer Vision course - Week 3 Milestone
