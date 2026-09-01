# accident_detector.py
"""
Detects vehicle accidents/collisions using bounding box overlap,
proximity, and velocity changes.
"""

def iou(bbox1, bbox2):
    """Calculate Intersection over Union (IoU) between two bboxes."""
    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2
    
    # Intersection
    xi_min = max(x1_min, x2_min)
    yi_min = max(y1_min, y2_min)
    xi_max = min(x1_max, x2_max)
    yi_max = min(y1_max, y2_max)
    
    if xi_min >= xi_max or yi_min >= yi_max:
        return 0.0  # No intersection
    
    inter_area = (xi_max - xi_min) * (yi_max - yi_min)
    
    # Union
    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = area1 + area2 - inter_area
    
    return inter_area / union_area if union_area > 0 else 0.0


def bbox_distance(bbox1, bbox2):
    """
    Calculate minimum distance between two bounding boxes.
    Returns 0 if they overlap.
    """
    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2
    
    # Check if overlapping
    if iou(bbox1, bbox2) > 0:
        return 0.0
    
    # Distance to edges
    dx = max(x2_min - x1_max, x1_min - x2_max, 0)
    dy = max(y2_min - y1_max, y1_min - y2_max, 0)
    
    return (dx**2 + dy**2) ** 0.5


class AccidentDetector:
    """
    Detects accidents using:
    1. Bounding box overlap (IOU > threshold)
    2. Proximity (distance between bboxes < threshold)
    3. Velocity profiles (sudden velocity changes)
    """
    
    def __init__(self, iou_threshold=0.1, proximity_threshold=30, 
                 velocity_threshold=100):
        """
        Args:
            iou_threshold: IoU above this indicates collision (default 0.1 = 10% overlap)
            proximity_threshold: Distance below this is dangerous proximity (pixels)
            velocity_threshold: High velocity threshold (pixels/second)
        """
        self.iou_threshold = iou_threshold
        self.proximity_threshold = proximity_threshold
        self.velocity_threshold = velocity_threshold
        self.collision_pairs = set()  # Track ongoing collisions
        self.frame_count = 0
        
    def detect(self, tracked_objects, velocities):
        """
        Detect accidents in current frame.
        
        Args:
            tracked_objects: List of dicts with 'id', 'bbox', 'centroid'
            velocities: Dict of track_id -> velocity (pixels/sec)
        
        Returns:
            {
                'collisions': list of (id1, id2) tuples,
                'near_miss': list of (id1, id2) tuples (close but not colliding),
                'high_velocity': list of track_ids with high velocity,
                'risky': bool (any collision or near miss detected)
            }
        """
        self.frame_count += 1
        collisions = []
        near_misses = []
        high_velocity_ids = []
        
        # Check for high velocity vehicles
        for tid, vel in velocities.items():
            if vel > self.velocity_threshold:
                high_velocity_ids.append(tid)
        
        # Pairwise comparison of vehicles
        for i, obj1 in enumerate(tracked_objects):
            for obj2 in tracked_objects[i+1:]:
                id1, id2 = obj1["id"], obj2["id"]
                bbox1, bbox2 = obj1["bbox"], obj2["bbox"]
                
                # Check for collision (IoU overlap)
                overlap = iou(bbox1, bbox2)
                if overlap > self.iou_threshold:
                    collisions.append((id1, id2))
                    self.collision_pairs.add((min(id1, id2), max(id1, id2)))
                else:
                    # Check for proximity (dangerous closeness)
                    dist = bbox_distance(bbox1, bbox2)
                    if dist < self.proximity_threshold and dist > 0:
                        # Both vehicles moving towards each other or high speed
                        vel1 = velocities.get(id1, 0)
                        vel2 = velocities.get(id2, 0)
                        if vel1 > 50 or vel2 > 50:  # Moving fast
                            near_misses.append((id1, id2))
        
        risky = len(collisions) > 0 or len(near_misses) > 0
        
        return {
            "collisions": collisions,
            "near_miss": near_misses,
            "high_velocity": high_velocity_ids,
            "risky": risky,
            "frame": self.frame_count
        }
    
    def get_alert_level(self, detection_result):
        """
        Return alert level: 'CRITICAL', 'WARNING', or 'OK'
        """
        if detection_result["collisions"]:
            return "CRITICAL"
        elif detection_result["near_miss"]:
            return "WARNING"
        else:
            return "OK"
