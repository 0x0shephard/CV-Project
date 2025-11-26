# Structure from Motion (SfM) Pipeline - CS 436 Project

This project implements a complete Structure from Motion pipeline, from feature matching to 3D reconstruction and interactive visualization.

## Author
Muhammad Jon Raza

## Project Overview
Building a Photosynth/Matterport-style 3D reconstruction and virtual tour system from 2D photographs.

## Current Status: Week 1 - Feature Matching ✅

### Week 1 Deliverable
- ✅ Feature detection using SIFT/ORB
- ✅ Feature matching with Lowe's ratio test
- ✅ Visualization of matched features between image pairs

## Project Structure
```
Project/
├── src/
│   └── feature_matching.py    # Feature detection and matching module
├── Data/                       # Input images for reconstruction
├── output/                     # Generated outputs (matches, point clouds, etc.)
├── notebooks/
│   └── week1_demo.ipynb       # Week 1 demonstration notebook
├── requirements.txt            # Python dependencies
└── README.md                   # This file
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

### Week 1: Feature Matching

#### Option 1: Command Line
```bash
# Activate virtual environment first
source venv/bin/activate

# Run feature matching on two images
python src/feature_matching.py "Data/WhatsApp Image 2025-11-13 at 14.35.58.jpeg" "Data/WhatsApp Image 2025-11-13 at 14.35.59.jpeg" output/matches.jpg
```

#### Option 2: Python Script
```python
from src.feature_matching import find_and_visualize_matches

results = find_and_visualize_matches(
    img1_path="Data/image1.jpeg",
    img2_path="Data/image2.jpeg",
    detector_type='SIFT',  # or 'ORB'
    ratio_threshold=0.75,
    num_matches_to_show=50,
    save_path="output/matches.jpg"
)

print(f"Found {len(results['matches'])} good matches")
```

#### Option 3: Jupyter Notebook
```bash
jupyter notebook notebooks/week1_demo.ipynb
```

#### Option 4: Batch Process All Pairs (22 images → 11 pairs)
```bash
# Process all consecutive image pairs in the Data folder
python src/process_all_pairs.py Data output SIFT

# This will:
# - Match all consecutive image pairs
# - Generate comparison visualizations
# - Identify the best pair for Week 2
# - Save all results to output/ folder
```

## Features Implemented

### Feature Detection
- **SIFT (Scale-Invariant Feature Transform)**: Robust to scale and rotation changes
- **ORB (Oriented FAST and Rotated BRIEF)**: Faster alternative to SIFT

### Feature Matching
- **Lowe's Ratio Test**: Filters matches by comparing distances of nearest and second-nearest neighbors
- **FLANN-based Matcher**: Fast approximate nearest neighbor matching for SIFT
- **Brute Force Matcher**: Hamming distance matching for ORB

### Visualization
- Keypoint detection visualization with size and orientation
- Side-by-side feature matching visualization
- Statistics and match quality metrics

## Data Collection Guidelines

For best results when capturing your own images:
1. **Move the camera** - don't just rotate in place (parallax is essential!)
2. **60-80% overlap** between consecutive images
3. **Consistent lighting** across all shots
4. **Sharp, in-focus images** without motion blur
5. **Textured scenes** - avoid blank walls or reflective surfaces
6. **15-30 images** total for a good reconstruction

## Upcoming Milestones

- **Week 2**: Two-View Reconstruction (Essential Matrix, Pose Recovery, Triangulation)
- **Week 3**: Multi-View SfM with PnP and Bundle Adjustment
- **Week 4**: Interactive Photosynth-style Visualization
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

- `output/matches.jpg`: Visualization of feature matches between image pairs
- `output/keypoints1.jpg`: First image with detected keypoints
- `output/keypoints2.jpg`: Second image with detected keypoints

## References

- Lowe, D. G. (2004). Distinctive Image Features from Scale-Invariant Keypoints
- Hartley, R., & Zisserman, A. (2003). Multiple View Geometry in Computer Vision
- Snavely, N., et al. (2006). Photo Tourism: Exploring Photo Collections in 3D

## License

This project is for educational purposes as part of CS 436 Computer Vision course.

---

**Note**: This is an academic project. The code is structured following professional software engineering practices with modular design, proper documentation, and version control.
