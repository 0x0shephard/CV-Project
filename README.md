# Structure from Motion (SfM) Pipeline - CS 436 Project

This project implements a complete Structure from Motion pipeline, from feature matching to 3D reconstruction and interactive visualization.

## Author
Muhammad Jon Raza, Hadi Shahzad

## Project Overview
Building a Photosynth/Matterport-style 3D reconstruction and virtual tour system from 2D photographs.

## Current Status: Week 3 - Multi-View SfM ✅

### Completed Milestones

#### Week 1: Feature Matching ✅
- ✅ Feature detection using SIFT/ORB
- ✅ Feature matching with Lowe's ratio test
- ✅ Visualization of matched features between image pairs

#### Week 2: Two-View Reconstruction ✅
- ✅ Essential matrix estimation with RANSAC
- ✅ Camera pose recovery with cheirality check
- ✅ 3D point triangulation
- ✅ PLY export for point cloud visualization

#### Week 3: Multi-View SfM & Bundle Adjustment ✅
- ✅ Incremental camera localization using PnP (Perspective-n-Point)
- ✅ Growing 3D map through triangulation
- ✅ Bundle Adjustment for global refinement
- ✅ Before/after comparison visualizations
- ✅ Professional modular code structure

## Project Structure
```
Project/
├── src/                          # Modular Python source code
│   ├── __init__.py              # Package initialization
│   ├── feature_matching.py     # Feature detection and matching
│   ├── two_view_geometry.py    # Two-view reconstruction
│   ├── incremental_sfm.py      # Incremental SfM with PnP
│   ├── bundle_adjustment.py    # Bundle Adjustment optimization
│   ├── visualization.py        # 3D visualization utilities
│   ├── io_utils.py             # I/O operations (load images, save PLY)
│   └── sfm_pipeline.py         # Complete pipeline orchestration
├── Data/                        # Input images for reconstruction
├── output/                      # Generated outputs
│   ├── week2/                  # Two-view reconstruction results
│   └── week3/                  # Multi-view SfM results
├── notebooks/
│   ├── week1_demo.ipynb        # Week 1: Feature matching
│   ├── week2_demo.ipynb        # Week 2: Two-view reconstruction (embedded in week1)
│   └── week3_demo.ipynb        # Week 3: Multi-view SfM & BA
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── COMPREHENSIVE_GUIDE.md       # Detailed technical documentation
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- macOS, Linux, or Windows

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start: Run Complete Pipeline

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the complete SfM pipeline on your images
python -m src.sfm_pipeline Data --output output/week3 --max-images 10

# This will:
# - Load images from Data/ directory
# - Initialize from two views
# - Incrementally add remaining views with PnP
# - Apply Bundle Adjustment for refinement
# - Export PLY files and visualizations
```

### Week 3: Multi-View SfM & Bundle Adjustment

#### Option 1: Interactive Notebook (Recommended)
```bash
jupyter notebook notebooks/week3_demo.ipynb
```
This provides a complete walkthrough with visualizations at each step.

#### Option 2: Python Script
```python
from src.sfm_pipeline import SfMPipeline

# Create pipeline
pipeline = SfMPipeline(
    image_dir="Data",
    output_dir="output/week3"
)

# Run complete pipeline
stats = pipeline.run_full_pipeline(
    image_pattern="*.jpg",
    max_images=10,
    detector_type='SIFT',
    run_ba=True
)

print(f"Reconstructed {stats['n_cameras']} cameras")
print(f"Generated {stats['n_points']} 3D points")
```

#### Option 3: Command Line with Options
```bash
# Process first 15 images with SIFT features
python -m src.sfm_pipeline Data --output output/week3 --max-images 15 --detector SIFT

# Process all images without Bundle Adjustment
python -m src.sfm_pipeline Data --output output/my_reconstruction --no-ba

# Custom image pattern
python -m src.sfm_pipeline Data --pattern "*.png" --output output/week3
```

### Previous Weeks

#### Week 1: Feature Matching
```bash
# See notebooks/week1_demo.ipynb for feature matching demonstrations
jupyter notebook notebooks/week1_demo.ipynb
```

#### Week 2: Two-View Reconstruction
Results are embedded in Week 1 notebook and serve as initialization for Week 3.

## Features Implemented

### Week 1: Feature Matching
- **SIFT/ORB Detection**: Scale and rotation invariant feature detection
- **Lowe's Ratio Test**: Robust feature match filtering
- **Visualization**: Keypoint and match visualizations

### Week 2: Two-View Geometry
- **Essential Matrix Estimation**: Using RANSAC for robustness
- **Pose Recovery**: Cheirality check to disambiguate camera pose
- **Triangulation**: 3D point reconstruction from two views
- **PLY Export**: Point cloud export for external visualization

### Week 3: Incremental SfM
- **PnP Camera Localization**: Estimate new camera poses using 2D-3D correspondences
- **Incremental Triangulation**: Grow 3D map by adding new views
- **Bundle Adjustment**: Global optimization using sparse least squares
  - Simultaneous refinement of all cameras and points
  - Minimize reprojection error across all observations
  - Scipy-based optimization with Jacobian sparsity
- **Professional Code Structure**: Modular design following software engineering best practices
- **Comprehensive Visualizations**:
  - Multiple viewpoint renderings
  - Camera trajectory plots
  - Before/after BA comparisons

## Data Collection Guidelines

For best results when capturing your own images:
1. **Move the camera** - don't just rotate in place (parallax is essential!)
2. **60-80% overlap** between consecutive images
3. **Consistent lighting** across all shots
4. **Sharp, in-focus images** without motion blur
5. **Textured scenes** - avoid blank walls or reflective surfaces
6. **15-30 images** total for a good reconstruction

## Upcoming Milestones

- **Week 4**: Interactive Photosynth-style Visualization
  - View graph construction
  - Smooth camera transitions (lerp/slerp)
  - Three.js-based web viewer
  - Image cross-fading during navigation
- **Week 5**: Final Report and Complete Submission

## Dependencies

- **OpenCV**: Computer vision operations (feature detection, matching, geometry)
- **NumPy**: Numerical computations and matrix operations
- **Matplotlib**: Visualization and plotting
- **Open3D**: 3D point cloud visualization (for later weeks)
- **Jupyter**: Interactive notebooks for demonstrations

## Troubleshooting

### Import Errors
Make sure you've activated the virtual environment and installed all dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Image Loading Issues
Ensure your image paths are correct and images are in a supported format (JPEG, PNG).

### Poor Matching Results
- Ensure images have significant overlap (60-80%)
- Try different detector types (SIFT vs ORB)
- Adjust ratio_threshold (0.7-0.8 typically works well)
- Make sure there's actual camera translation (parallax), not just rotation

## Output Files

### Week 1 Output
- `output/pair_XX_matches.jpg`: Feature match visualizations
- `output/all_pairs_summary.csv`: Statistics for all image pairs

### Week 2 Output
- `output/week2/reconstruction.ply`: 3D point cloud from two views
- `output/week2/3d_visualization.png`: Multiple viewpoint renderings

### Week 3 Output
- `output/week3/reconstruction_two_view.ply`: Initial 2-view reconstruction
- `output/week3/reconstruction_before_ba.ply`: Before bundle adjustment
- `output/week3/reconstruction_after_ba.ply`: After bundle adjustment (refined)
- `output/week3/reconstruction_refined.ply`: Final result (same as after BA)
- `output/week3/reconstruction_multiview.png`: Multiple viewpoints of final reconstruction
- `output/week3/camera_trajectory.png`: Estimated camera path
- `output/week3/ba_comparison.png`: Before/after comparison
- `output/week3/reconstruction_summary.txt`: Detailed statistics

## References

- Lowe, D. G. (2004). Distinctive Image Features from Scale-Invariant Keypoints
- Hartley, R., & Zisserman, A. (2003). Multiple View Geometry in Computer Vision
- Snavely, N., et al. (2006). Photo Tourism: Exploring Photo Collections in 3D

## License

This project is for educational purposes as part of CS 436 Computer Vision course.

---

**Note**: This is an academic project. The code is structured following professional software engineering practices with modular design, proper documentation, and version control.
