"""
SafeFall AI — Fall Detection & Pose Estimation Engine
Supports webcam vision processing via OpenCV/MediaPipe (when available)
with automatic graceful degradation and synthetic simulation frames.
"""

import math
import time
from typing import Tuple, Dict, Any, Optional
import numpy as np

# Optional imports for OpenCV & MediaPipe
OPENCV_AVAILABLE = False
MEDIAPIPE_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except (ImportError, Exception):
    mp = None


def check_vision_support() -> Dict[str, Any]:
    """Check availability of OpenCV and MediaPipe libraries."""
    return {
        "opencv": OPENCV_AVAILABLE,
        "mediapipe": MEDIAPIPE_AVAILABLE,
        "status": "Ready" if (OPENCV_AVAILABLE and MEDIAPIPE_AVAILABLE) else "Fallback Mode Available",
        "details": (
            "OpenCV & MediaPipe available for live camera pose estimation."
            if (OPENCV_AVAILABLE and MEDIAPIPE_AVAILABLE)
            else "Camera pose estimation running in fallback/synthetic mode. Simulated triggers fully operational."
        )
    }


class VisionFallDetector:
    """Pose-based potential fall detection utilizing MediaPipe Pose landmarks."""

    def __init__(self, min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.pose = None
        self.mp_drawing = None
        self.mp_pose = None
        self.initialized = False

        if OPENCV_AVAILABLE and MEDIAPIPE_AVAILABLE:
            try:
                self.mp_pose = mp.solutions.pose
                self.mp_drawing = mp.solutions.drawing_utils
                self.pose = self.mp_pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    enable_segmentation=False,
                    min_detection_confidence=min_detection_confidence,
                    min_tracking_confidence=min_tracking_confidence
                )
                self.initialized = True
                self.backend = "MediaPipe Pose Landmark Model"
            except Exception as e:
                self.initialized = False
                self.backend = "Disabled"
        elif OPENCV_AVAILABLE:
            # Native OpenCV contour & aspect-ratio heuristic analyzer
            self.initialized = True
            self.backend = "OpenCV Silhouette & Aspect Ratio Posture Analyzer"
        else:
            self.initialized = False
            self.backend = "Disabled"

    def process_frame(self, frame_bgr: np.ndarray) -> Tuple[np.ndarray, bool, Dict[str, Any]]:
        """
        Analyze a single video frame for potential fall posture.

        Returns:
            annotated_frame: Frame with visual skeleton/contour overlays and telemetry
            is_potential_fall: True if pose signals suggest a fallen posture
            telemetry: Dictionary containing angle, aspect ratio, confidence, and status
        """
        if not self.initialized or frame_bgr is None:
            return frame_bgr, False, {"error": "Vision pipeline not initialized"}

        h, w, _ = frame_bgr.shape
        annotated = frame_bgr.copy()

        # If MediaPipe Pose is available, use landmarks
        if MEDIAPIPE_AVAILABLE and self.pose is not None:
            try:
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                results = self.pose.process(frame_rgb)
                if results and results.pose_landmarks:
                    telemetry["landmarks_detected"] = True
                    landmarks = results.pose_landmarks.landmark

                    # Extract key joints: Left/Right Shoulders and Left/Right Hips
                    ls = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
                    rs = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
                    lh = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
                    rh = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]

                    # Midpoints
                    shoulder_mid_x = (ls.x + rs.x) / 2.0
                    shoulder_mid_y = (ls.y + rs.y) / 2.0
                    hip_mid_x = (lh.x + rh.x) / 2.0
                    hip_mid_y = (lh.y + rh.y) / 2.0

                    # Torso angle relative to horizontal plane
                    dx = shoulder_mid_x - hip_mid_x
                    dy = shoulder_mid_y - hip_mid_y
                    angle_rad = math.atan2(abs(dy), abs(dx))
                    angle_deg = math.degrees(angle_rad)

                    visible_x = [lm.x for lm in landmarks if lm.visibility > 0.4]
                    visible_y = [lm.y for lm in landmarks if lm.visibility > 0.4]

                    if visible_x and visible_y:
                        bbox_w = (max(visible_x) - min(visible_x)) * w
                        bbox_h = (max(visible_y) - min(visible_y)) * h
                        aspect_ratio = bbox_w / max(bbox_h, 1.0)
                    else:
                        aspect_ratio = 0.5

                    vertical_center = (shoulder_mid_y + hip_mid_y) / 2.0
                    avg_vis = (ls.visibility + rs.visibility + lh.visibility + rh.visibility) / 4.0

                    is_horizontal = angle_deg < 42.0
                    is_low_to_ground = vertical_center > 0.62
                    is_wide_bbox = aspect_ratio > 1.15

                    if (is_horizontal and (is_low_to_ground or is_wide_bbox)) and avg_vis > 0.45:
                        is_fall = True
                        posture = "POTENTIAL FALL DETECTED (Horizontal Posture)"
                        color = (0, 0, 255)
                    elif angle_deg < 55.0 and avg_vis > 0.45:
                        posture = "Unstable / Reclined"
                        color = (0, 215, 255)
                    else:
                        posture = "Upright / Stable"
                        color = (0, 255, 0)

                    telemetry.update({
                        "torso_angle_deg": round(angle_deg, 1),
                        "aspect_ratio": round(aspect_ratio, 2),
                        "vertical_center": round(vertical_center, 2),
                        "confidence": round(avg_vis, 2),
                        "posture": posture
                    })

                    self.mp_drawing.draw_landmarks(
                        annotated,
                        results.pose_landmarks,
                        self.mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=3),
                        connection_drawing_spec=self.mp_drawing.DrawingSpec(color=color, thickness=2)
                    )

                    overlay_text = f"Status: {posture} | Spine Angle: {telemetry['torso_angle_deg']} deg"
                    cv2.putText(annotated, overlay_text, (20, 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
            except Exception:
                pass

        elif OPENCV_AVAILABLE:
            # OpenCV native silhouette / contour aspect-ratio posture analysis
            try:
                gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (7, 7), 0)
                edges = cv2.Canny(blurred, 50, 150)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    c = max(contours, key=cv2.contourArea)
                    x, y, bw, bh = cv2.boundingRect(c)
                    aspect_ratio = bw / max(bh, 1.0)
                    vertical_center = (y + bh / 2.0) / h
                    is_horizontal = aspect_ratio > 1.2
                    is_low = vertical_center > 0.60

                    if is_horizontal or is_low:
                        is_fall = True
                        posture = "POTENTIAL FALL DETECTED (Horizontal Silhouette)"
                        color = (0, 0, 255)
                    else:
                        posture = "Upright / Stable Posture"
                        color = (0, 255, 0)

                    cv2.rectangle(annotated, (x, y), (x + bw, y + bh), color, 2)
                    telemetry.update({
                        "landmarks_detected": True,
                        "torso_angle_deg": round(math.degrees(math.atan2(bh, bw)), 1),
                        "aspect_ratio": round(aspect_ratio, 2),
                        "vertical_center": round(vertical_center, 2),
                        "confidence": 0.80,
                        "posture": posture
                    })
                    cv2.putText(annotated, f"OpenCV Pose: {posture}", (20, 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            except Exception:
                pass

        disclaimer_text = "Signal: Potential Fall Indicator (Not Medical Diagnostic)"
        if OPENCV_AVAILABLE:
            cv2.putText(annotated, disclaimer_text, (20, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        return annotated, is_fall, telemetry


def generate_synthetic_demo_frame(mode: str = "standing", width: int = 640, height: int = 400) -> np.ndarray:
    """
    Generate an illustrative synthetic camera frame with drawn stick-figure & room aesthetics.
    Used for live visual demonstration when a physical webcam is not attached or permitted.
    """
    # Create dark room background
    canvas = np.full((height, width, 3), 28, dtype=np.uint8)

    # Room perspective grid lines (floor & walls)
    floor_y = int(height * 0.72)
    # Floor fill
    canvas[floor_y:, :] = (40, 42, 45)

    if not OPENCV_AVAILABLE:
        return canvas

    # Draw room horizon
    cv2.line(canvas, (0, floor_y), (width, floor_y), (70, 75, 80), 2)
    cv2.line(canvas, (0, int(height * 0.2)), (int(width * 0.25), floor_y), (60, 65, 70), 1)
    cv2.line(canvas, (width, int(height * 0.2)), (int(width * 0.75), floor_y), (60, 65, 70), 1)

    cx = width // 2

    if mode == "fallen":
        # Lying horizontally on the floor
        head_pos = (cx - 110, floor_y + 35)
        shoulder_pos = (cx - 60, floor_y + 40)
        hip_pos = (cx + 30, floor_y + 42)
        knee_pos = (cx + 90, floor_y + 38)
        foot_pos = (cx + 140, floor_y + 42)

        # Draw fallen person (Red)
        color = (60, 60, 230)  # Red BGR
        cv2.circle(canvas, head_pos, 16, color, -1)
        cv2.line(canvas, head_pos, shoulder_pos, color, 4)
        cv2.line(canvas, shoulder_pos, hip_pos, color, 4)
        cv2.line(canvas, hip_pos, knee_pos, color, 4)
        cv2.line(canvas, knee_pos, foot_pos, color, 4)

        # Arms
        cv2.line(canvas, shoulder_pos, (cx - 40, floor_y + 15), color, 3)

        # Telemetry HUD
        cv2.putText(canvas, "[SIMULATED SENSOR FEED: FALL EVENT]", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (50, 50, 255), 2)
        cv2.putText(canvas, "Spine Angle: 12.4 deg | Posture: Horizontal Grounded", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 255), 1)
        cv2.putText(canvas, "ALERT: Potential Fall Posture Detected", (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)

    elif mode == "stumbling":
        # Off-balance tilted figure
        head_pos = (cx + 40, floor_y - 120)
        shoulder_pos = (cx + 20, floor_y - 85)
        hip_pos = (cx - 10, floor_y - 40)
        knee_left = (cx - 40, floor_y - 15)
        foot_left = (cx - 50, floor_y)
        knee_right = (cx + 20, floor_y - 15)
        foot_right = (cx + 30, floor_y)

        color = (0, 215, 255)  # Yellow BGR
        cv2.circle(canvas, head_pos, 16, color, -1)
        cv2.line(canvas, head_pos, shoulder_pos, color, 4)
        cv2.line(canvas, shoulder_pos, hip_pos, color, 4)
        cv2.line(canvas, hip_pos, knee_left, color, 4)
        cv2.line(canvas, knee_left, foot_left, color, 4)
        cv2.line(canvas, hip_pos, knee_right, color, 4)
        cv2.line(canvas, knee_right, foot_right, color, 4)
        # Arms flailing
        cv2.line(canvas, shoulder_pos, (cx - 30, floor_y - 95), color, 3)
        cv2.line(canvas, shoulder_pos, (cx + 70, floor_y - 80), color, 3)

        cv2.putText(canvas, "[SIMULATED SENSOR FEED: UNSTABLE MOTION]", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 215, 255), 2)
        cv2.putText(canvas, "Spine Angle: 44.8 deg | Posture: Rapid Trajectory Tilt", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 215, 255), 1)

    else:
        # Standing upright figure (Green)
        head_pos = (cx, floor_y - 150)
        shoulder_pos = (cx, floor_y - 115)
        hip_pos = (cx, floor_y - 65)
        knee_pos = (cx, floor_y - 30)
        foot_pos = (cx, floor_y)

        color = (0, 220, 100)  # Green BGR
        cv2.circle(canvas, head_pos, 16, color, -1)
        cv2.line(canvas, head_pos, shoulder_pos, color, 4)
        cv2.line(canvas, shoulder_pos, hip_pos, color, 4)
        cv2.line(canvas, hip_pos, knee_pos, color, 4)
        cv2.line(canvas, knee_pos, foot_pos, color, 4)
        # Arms resting at side
        cv2.line(canvas, shoulder_pos, (cx - 20, floor_y - 70), color, 3)
        cv2.line(canvas, shoulder_pos, (cx + 20, floor_y - 70), color, 3)

        cv2.putText(canvas, "[SIMULATED SENSOR FEED: NORMAL MONITORING]", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 100), 2)
        cv2.putText(canvas, "Spine Angle: 88.5 deg | Posture: Upright / Nominal", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 220, 180), 1)

    # Prototype disclaimer watermark
    cv2.putText(canvas, "SafeFall AI Demo Vision Channel - Simulated Frame", (20, height - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (150, 150, 150), 1)

    return canvas
