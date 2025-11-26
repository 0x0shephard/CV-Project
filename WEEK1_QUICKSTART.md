# Week 1 Quick Start Guide
## Feature Matching for Structure from Motion

### What You Have Now

Your Week 1 implementation includes:

1. **Feature Matching Module** (`src/feature_matching.py`)
   - SIFT and ORB feature detection
   - Lowe's ratio test for match filtering
   - Comprehensive visualization functions

2. **Jupyter Notebook** (`notebooks/week1_demo.ipynb`)
   - Step-by-step feature matching tutorial
   - **Bonus: Process all 11 consecutive image pairs**
   - Automatic identification of best pairs for Week 2
   - Comprehensive statistics and visualizations

3. **Batch Processing Script** (`src/process_all_pairs.py`)
   - Command-line tool to process all image pairs at once
   - Generates summary CSV and visualizations
   - Saves best pair data for Week 2

### Setup (First Time Only)

```bash
# 1. Navigate to project directory
cd /Users/muhammadjonraza/Desktop/CV/Project

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt
```

### How to Run

#### Option 1: Run the Full Notebook (Recommended)

```bash
# Start Jupyter
jupyter notebook notebooks/week1_demo.ipynb

# Then run all cells (Cell → Run All)
```

This will:
- Process your first image pair step-by-step
- **Process all 22 images (11 pairs)** automatically
- Generate comparison charts
- Identify the top 3 best pairs for Week 2
- Save all results to `output/` folder

#### Option 2: Command Line (Quick Processing)

```bash
# Process all pairs at once
python src/process_all_pairs.py Data output SIFT
```

#### Option 3: Test Single Pair

```bash
# Test on one pair
python src/feature_matching.py \
  "Data/WhatsApp Image 2025-11-13 at 14.35.58.jpeg" \
  "Data/WhatsApp Image 2025-11-13 at 14.35.59.jpeg" \
  output/test_matches.jpg
```

### What Gets Generated

After running, check the `output/` folder:

```
output/
├── pair_01_matches.jpg       # Pair 1 matches visualization
├── pair_02_matches.jpg       # Pair 2 matches visualization
├── ...                       # (11 pairs total)
├── pair_11_matches.jpg       # Pair 11 matches visualization
├── best_pair_matches.jpg     # Best pair (top 100 matches)
├── best_pair_matched_points.npz  # Saved for Week 2!
├── all_pairs_summary.csv     # Statistics table
└── all_pairs_summary.png     # Comparison charts
```

### Understanding the Results

The notebook/script will identify the **best image pair** based on:
- **Number of matches**: More matches = more feature correspondences
- **Match quality**: Lower average distance = better matches
- **Quality score**: Combines both metrics

Use this best pair for Week 2's two-view reconstruction!

### Expected Output

For 22 images, you should see:
- **11 consecutive pairs** processed
- **~200-1000 matches per pair** (depending on scene overlap)
- **Quality comparison charts** showing which pairs are best
- **Recommendation** for Week 2

### Troubleshooting

**Problem**: Import errors
```bash
# Solution: Make sure virtual environment is activated and packages installed
source venv/bin/activate
pip install -r requirements.txt
```

**Problem**: No images found
```bash
# Solution: Check that images are in Data/ folder
ls Data/
```

**Problem**: Few matches (< 50)
- Check that images have 60-80% overlap
- Ensure camera moved (parallax), not just rotated
- Try different consecutive pairs

### Next Steps (Week 2)

The notebook saves `output/best_pair_matched_points.npz` which contains:
- `pts1`: Matched points in image 1
- `pts2`: Corresponding points in image 2
- `img1_path`: Path to image 1
- `img2_path`: Path to image 2

Use these for:
- Essential matrix estimation
- Camera pose recovery
- 3D point triangulation

### Tips for Best Results

1. **Run the notebook first** - It's educational and comprehensive
2. **Check the visualizations** - Verify matches look geometrically consistent
3. **Use the recommended best pair** - It will give best reconstruction results
4. **Save your output folder** - You'll need it for Week 2

### Quick Commands Summary

```bash
# Activate environment
source venv/bin/activate

# Run Jupyter notebook (RECOMMENDED)
jupyter notebook notebooks/week1_demo.ipynb

# OR batch process
python src/process_all_pairs.py Data output SIFT

# View results
open output/all_pairs_summary.png
open output/best_pair_matches.jpg
```

---

## Week 1 Deliverable Checklist ✅

- [x] Feature detection implemented (SIFT/ORB)
- [x] Lowe's ratio test for match filtering
- [x] Visualization of matched features
- [x] Process all 11 image pairs
- [x] Identify best pairs for Week 2
- [x] Save matched points for reconstruction
- [x] Professional code structure and documentation

**You're ready for Week 2! 🚀**
