"""
VisionTraceAI — Pose-based Kinematics Engine.

Calculates rolling-window velocities of human skeletal keypoints
to classify actions (e.g., 'running', 'walking', 'standing').
"""

import math
from collections import defaultdict
from typing import Dict, List, Any

class KinematicsEngine:
    def __init__(self, window_size: int = 15, fps: float = 30.0):
        self.window_size = window_size
        self.fps = fps
        # Buffer maps track_id -> list of keypoint payloads (x, y coords)
        self.history: Dict[int, List[Dict[str, float]]] = defaultdict(list)
        
        # Velocity thresholds (pixels per second, rough approximation)
        self.RUNNING_THRESHOLD = 300.0
        self.WALKING_THRESHOLD = 50.0

    def _calculate_center_of_mass(self, keypoints: List[float]) -> tuple[float, float]:
        """
        Calculates the center of mass based on YOLO11-pose 17 keypoints.
        YOLO-pose format is typically [x, y, conf] for 17 points per person.
        We average the valid (conf > 0.5) points.
        """
        valid_x = []
        valid_y = []
        
        # Keypoints array is flat or [17, 2/3] shape. Assuming standard flattened [x1,y1, x2,y2, ...]
        # or list of [x, y] tuples.
        
        # Ultralytics results.keypoints.xy is typically a tensor of shape (N, 17, 2).
        # We expect keypoints to be a list of [x, y] coordinates.
        for kp in keypoints:
            x, y = kp[0], kp[1]
            if x > 0 and y > 0:
                valid_x.append(x)
                valid_y.append(y)
                
        if not valid_x:
            return 0.0, 0.0
            
        return sum(valid_x) / len(valid_x), sum(valid_y) / len(valid_y)

    def update_and_classify(self, track_id: int, keypoints: List[Any]) -> str:
        """
        Adds the current keypoints to the window and computes the action.
        """
        cx, cy = self._calculate_center_of_mass(keypoints)
        
        if cx == 0.0 and cy == 0.0:
            return "unknown"
            
        self.history[track_id].append({"x": cx, "y": cy})
        
        # Maintain rolling window
        if len(self.history[track_id]) > self.window_size:
            self.history[track_id].pop(0)
            
        # Need at least a few frames to calculate velocity
        if len(self.history[track_id]) < 5:
            return "unknown"
            
        # Calculate velocity over the window
        start = self.history[track_id][0]
        end = self.history[track_id][-1]
        
        dx = end["x"] - start["x"]
        dy = end["y"] - start["y"]
        distance = math.sqrt(dx**2 + dy**2)
        
        # Time elapsed in seconds
        dt = len(self.history[track_id]) / self.fps
        velocity = distance / dt
        
        if velocity > self.RUNNING_THRESHOLD:
            return "running"
        elif velocity > self.WALKING_THRESHOLD:
            return "walking"
        else:
            return "standing"

    def cleanup_track(self, track_id: int) -> None:
        if track_id in self.history:
            del self.history[track_id]
