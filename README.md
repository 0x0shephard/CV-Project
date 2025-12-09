# Structure from Motion (SfM) Pipeline - CS 436 Project

**Authors:** Muhammad Jon Raza, Hadi Shahzad
**Course:** CS 436 - Computer Vision



## Quick Start

```bash
# 1. Clone and navigate to project
cd CV-Project-

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the complete pipeline (fastest method)
python test_pipeline.py

# 5. Open the interactive viewer
open viewer/index.html  # macOS
# Or: start viewer/index.html  (Windows)
# Or: xdg-open viewer/index.html  (Linux)
```

That's it! You now have a 3D reconstruction with an interactive viewer.

---

## Setup Instructions


### Installation Steps

#### 1. Create Virtual Environment

```bash
python3 -m venv venv
```

#### 2. Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `opencv-contrib-python` - Computer vision operations
- `numpy` - Numerical computations
- `matplotlib` - Visualization
- `scipy` - Optimization (Bundle Adjustment)
- `jupyter` - Interactive notebooks
- Additional utilities (pandas, weasyprint, etc.)

#### 4. Verify Installation

```bash
python -c "import cv2, numpy, scipy, matplotlib; print('✓ All dependencies installed')"
```

---

## Running the Pipeline

### Method 1: Quick Pipeline Test (Recommended for First Run)

The fastest way to run the complete SfM pipeline:

```bash
# Activate virtual environment
source venv/bin/activate

# Run pipeline on first few image pairs
python test_pipeline.py
```


### Method 2: Interactive Jupyter Notebooks (Recommended for Learning)

Step-by-step demonstrations with visualizations:

#### Week 1: Feature Matching
```bash
jupyter notebook notebooks/week1_demo.ipynb
```
- SIFT/ORB feature detection
- Feature matching visualization
- Lowe's ratio test filtering

#### Week 3: Multi-View SfM & Bundle Adjustment
```bash
jupyter notebook notebooks/week3_demo.ipynb
```
- Complete SfM pipeline walkthrough
- Incremental camera registration
- Bundle Adjustment optimization
- Before/after comparisons

#### Week 4: Interactive Viewer
```bash
jupyter notebook notebooks/week4_demo.ipynb
```
- Exporting to web format
- Covisibility graph construction
- Camera interpolation techniques



## Interactive 3D Viewer

**Option 2: Local Web Server (Recommended)**
```bash
# Python 3
cd viewer
python -m http.server 8000
# Open browser to http://localhost:8000

# Or use any other local server
```

### Viewer Features

- **3D Point Cloud**: Visualize ~45,000 reconstructed points with colors
- **Camera Positions**: See all 26 registered camera poses
- **Navigation**:
  - Mouse: Orbit, pan, zoom the scene
  - Keyboard: Jump between camera views
- **Smooth Transitions**: Lerp (position) + Slerp (rotation)
- **Covisibility Graph**: Cameras connected by shared 3D points
- **Image Overlay**: Original photographs displayed at camera positions

### Viewer Controls

| Control | Action |
|---------|--------|
| Left Mouse + Drag | Rotate camera |
| Right Mouse + Drag | Pan view |
| Mouse Wheel | Zoom in/out |
| Number Keys (1-9) | Jump to camera view |
| Arrow Keys | Navigate between cameras |
| R | Reset to default view |
| H | Toggle help panel |

---

## Project Structure

```
CV-Project-/
├── Data/                          # Input images (26 DSLR photos, 6048×4032px)
│   ├── DSC_0803.JPG
│   ├── DSC_0816.JPG to DSC_0843.JPG
│   └── ... (26 total images)
│
├── src/                           # Core Python modules
│   ├── __init__.py                # Package initialization
│   ├── camera.py                  # Intrinsic matrix construction
│   ├── feature_matching.py        # SIFT detection & Lowe's ratio test
│   ├── two_view_geometry.py       # Essential matrix, pose, triangulation
│   ├── two_view_reconstruction.py # 2-view reconstruction helpers
│   ├── incremental_sfm.py         # IncrementalMapper class (PnP)
│   ├── bundle_adjustment.py       # Global optimization
│   ├── utils.py                   # PLY export, statistics
│   ├── export_to_web.py           # JSON export for viewer
│   ├── export_colmap.py           # COLMAP format export (optional)
│   └── convert_colmap.py          # COLMAP conversion utilities
│
├── notebooks/                     # Jupyter demonstration notebooks
│   ├── week1_demo.ipynb           # Feature matching
│   ├── week3_demo.ipynb           # Multi-view SfM & BA
│   └── week4_demo.ipynb           # Interactive viewer demo
│
├── viewer/                        # Interactive Three.js web viewer
│   ├── index.html                 # Main HTML page
│   ├── style.css                  # Styling
│   ├── js/
│   │   └── main.js                # Viewer JavaScript logic
│   └── assets/
│       ├── data.json              # Camera poses & covisibility graph
│       ├── model.ply              # Reconstructed point cloud
│       └── images/                # Source images for overlay
│
├── output/                        # Generated outputs
│   ├── week2/                     # Two-view reconstruction results
│   ├── week3/                     # Multi-view SfM results
│   │   ├── reconstruction_before_ba.ply
│   │   ├── reconstruction_after_ba.ply
│   │   ├── camera_trajectory.png
│   │   └── reconstruction_summary.txt
│   ├── *.jpg                      # Feature match visualizations
│   └── statistics.txt             # Overall statistics
│
├── test_pipeline.py               # Quick pipeline test script
├── requirements.txt               # Python dependencies
├── Final_Report.md                # Project report (Markdown)
├── Final_Report.pdf               # Project report (PDF)
└── README.md                      # This file
```

---

## Features & Algorithms

### Week 1: Feature Matching

**SIFT (Scale-Invariant Feature Transform)**
- Detects ~107,000 keypoints per 6048×4032 image
- 128-dimensional descriptors per keypoint
- Scale and rotation invariant

**FLANN Matcher**
- Fast Library for Approximate Nearest Neighbors
- KD-tree indexing for efficient matching
- ~15,000 raw matches per image pair

**Lowe's Ratio Test**
- Filters matches using 0.75 threshold
- Keeps matches where d1/d2 < 0.75
- Results: ~5,400 high-quality matches per pair

### Week 2: Two-View Geometry

**Essential Matrix Estimation**
- RANSAC-based robust estimation
- Parameters: prob=0.999, threshold=1.0 pixel
- ~36% inlier rate (5,370 out of 14,799)

**Camera Pose Recovery**
- Decomposes essential matrix (4 possible poses)
- Cheirality check selects correct pose
- Ensures points are in front of both cameras

**Triangulation**
- `cv2.triangulatePoints()` for 3D reconstruction
- Converts matched 2D points to 3D coordinates
- Initial reconstruction: ~4,845 3D points

**Depth Filtering**
- Validates positive depth for both cameras
- Removes outliers behind cameras
- Filters unreliable triangulations

### Week 3: Incremental SfM & Bundle Adjustment

**PnP (Perspective-n-Point)**
- `cv2.solvePnPRansac()` for new camera localization
- Requires minimum 40 2D-3D correspondences
- Reprojection threshold: 3.0 pixels
- Estimates 6-DOF camera pose (3 rotation + 3 translation)

**Incremental Triangulation**
- Grows 3D map by adding new views
- Triangulates matches between registered cameras
- Final map: ~45,000 3D points from 26 cameras

**Bundle Adjustment**
- Minimizes: Σ ||x_ij - π(K, R_i, t_i, X_j)||²
- Parameters: 6 per camera + 3 per point
- Optimizer: `scipy.optimize.least_squares`
- Method: Trust Region Reflective (TRF)
- Results: RMSE 2.5-3.0 → 1.2-1.5 pixels

**Sparse Jacobian**
- Exploits sparsity in observation structure
- Camera i only affects points observed by i
- Point j only affects cameras observing j
- Significant speedup for large reconstructions

### Week 4: Interactive Visualization

**Covisibility Graph**
- Connects cameras sharing ≥30 common 3D points
- Enables smooth navigation between related views
- Graph structure stored in JSON

**Coordinate System Conversion**
- OpenCV: Y-down, Z-forward (camera convention)
- Three.js: Y-up, Z-backward (graphics convention)
- Automatic transformation during export

**Camera Interpolation**
- **Position**: Linear interpolation (lerp)
  - `P(t) = P₀ + t(P₁ - P₀)`
- **Rotation**: Spherical linear interpolation (slerp)
  - Quaternion interpolation for smooth rotation
  - Avoids gimbal lock issues

**Three.js Renderer**
- WebGL-based point cloud rendering
- Camera frustum helpers
- OrbitControls for interactive navigation
- PLYLoader for point cloud loading

---

## Output Files

### Week 1 Outputs

**Feature Match Visualizations**
- `output/DSC_XXXX_matches.jpg` - Feature match images
- Shows keypoints and correspondences between image pairs

### Week 2 Outputs

**Two-View Reconstruction**
- `output/week2/reconstruction.ply` - Initial 3D point cloud (~4,845 points)
- `output/week2/3d_visualization.png` - Multiple viewpoint renderings

### Week 3 Outputs

**Multi-View SfM Results**
- `reconstruction_two_view.ply` - Initial 2-view reconstruction
- `reconstruction_before_ba.ply` - Before Bundle Adjustment (~45k points)
- `reconstruction_after_ba.ply` - After Bundle Adjustment (refined)
- `reconstruction_refined.ply` - Final result (same as after BA)

**Visualizations**
- `reconstruction_multiview.png` - Multiple viewpoints of reconstruction
- `camera_trajectory.png` - Estimated camera path through scene
- `ba_comparison.png` - Before/after Bundle Adjustment comparison

**Statistics**
- `reconstruction_summary.txt` - Detailed statistics:
  - Number of cameras registered
  - Number of 3D points
  - Reprojection errors (before/after BA)
  - Point cloud density metrics

### Week 4 Outputs

**Interactive Viewer Assets**
- `viewer/assets/data.json` - Camera poses + covisibility graph
- `viewer/assets/model.ply` - Final point cloud
- `viewer/assets/images/` - Original images for overlay

