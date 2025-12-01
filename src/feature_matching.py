"""Feature detection and matching using SIFT/ORB with Lowe's ratio test."""

from __future__ import annotations

import cv2
import numpy as np
from typing import Tuple, List
from .two_view_geometry import FeatureSet, MatchResult


class FeatureMatcher:
    """Feature detector and matcher using SIFT or ORB."""

    def __init__(self, detector_type: str = 'SIFT', ratio_threshold: float = 0.75):
        """
        Initialize feature matcher.

        Args:
            detector_type: 'SIFT' or 'ORB'
            ratio_threshold: Lowe's ratio test threshold
        """
        self.detector_type = detector_type
        self.ratio_threshold = ratio_threshold

        if detector_type == 'SIFT':
            self.detector = cv2.SIFT_create()
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            self.matcher = cv2.FlannBasedMatcher(index_params, search_params)
        elif detector_type == 'ORB':
            self.detector = cv2.ORB_create(nfeatures=2000)
            FLANN_INDEX_LSH = 6
            index_params = dict(algorithm=FLANN_INDEX_LSH,
                               table_number=6,
                               key_size=12,
                               multi_probe_level=1)
            search_params = dict(checks=50)
            self.matcher = cv2.FlannBasedMatcher(index_params, search_params)
        else:
            raise ValueError(f"Unknown detector type: {detector_type}")

    def detect_and_compute(self, image: np.ndarray) -> Tuple[List, np.ndarray]:
        """
        Detect keypoints and compute descriptors.

        Args:
            image: Input image (BGR)

        Returns:
            Tuple of (keypoints, descriptors)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        keypoints, descriptors = self.detector.detectAndCompute(gray, None)
        return keypoints, descriptors

    def match_features(self, desc1: np.ndarray, desc2: np.ndarray) -> List[cv2.DMatch]:
        """
        Match features using Lowe's ratio test.

        Args:
            desc1: Descriptors from image 1
            desc2: Descriptors from image 2

        Returns:
            List of good matches
        """
        if desc1 is None or desc2 is None or len(desc1) < 2 or len(desc2) < 2:
            return []

        if self.detector_type == 'ORB':
            desc1 = desc1.astype(np.uint8)
            desc2 = desc2.astype(np.uint8)

        matches = self.matcher.knnMatch(desc1, desc2, k=2)

        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < self.ratio_threshold * n.distance:
                    good_matches.append(m)

        return good_matches


def match_features(featureset1: FeatureSet, featureset2: FeatureSet, ratio_threshold: float = 0.75) -> MatchResult:
    """
    Match features between two feature sets using Lowe's ratio test.

    Args:
        featureset1: FeatureSet from image 1
        featureset2: FeatureSet from image 2
        ratio_threshold: Lowe's ratio test threshold

    Returns:
        MatchResult with matches and point correspondences
    """
    matcher = FeatureMatcher(detector_type='SIFT', ratio_threshold=ratio_threshold)
    matches = matcher.match_features(featureset1.descriptors, featureset2.descriptors)

    if not matches:
        return MatchResult(
            matches=[],
            idx1=np.array([], dtype=np.int32),
            idx2=np.array([], dtype=np.int32),
            pts1=np.empty((0, 2), dtype=np.float32),
            pts2=np.empty((0, 2), dtype=np.float32)
        )

    idx1 = np.array([m.queryIdx for m in matches], dtype=np.int32)
    idx2 = np.array([m.trainIdx for m in matches], dtype=np.int32)
    pts1 = np.array([featureset1.keypoints[m.queryIdx].pt for m in matches], dtype=np.float32)
    pts2 = np.array([featureset2.keypoints[m.trainIdx].pt for m in matches], dtype=np.float32)

    return MatchResult(
        matches=matches,
        idx1=idx1,
        idx2=idx2,
        pts1=pts1,
        pts2=pts2
    )
