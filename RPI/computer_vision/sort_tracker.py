import numpy as np
from collections import deque

class Track:
    def __init__(self, bbox, track_id):
        self.bbox = bbox
        self.id = track_id
        self.missed = 0

class SortTracker:
    def __init__(self, max_missed=5, iou_threshold=0.3):
        self.tracks = []
        self.next_id = 1
        self.max_missed = max_missed
        self.iou_threshold = iou_threshold

    def iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[0]+boxA[2], boxB[0]+boxB[2])
        yB = min(boxA[1]+boxA[3], boxB[1]+boxB[3])

        inter = max(0, xB-xA) * max(0, yB-yA)
        areaA = boxA[2] * boxA[3]
        areaB = boxB[2] * boxB[3]

        union = areaA + areaB - inter
        return inter / union if union > 0 else 0

    def update(self, detections):
        assigned = set()

        # Match detections to existing tracks
        for track in self.tracks:
            best_iou = 0
            best_det = -1

            for i, det in enumerate(detections):
                if i in assigned:
                    continue
                iou_score = self.iou(track.bbox, det)

                if iou_score > best_iou:
                    best_iou = iou_score
                    best_det = i

            if best_iou > self.iou_threshold:
                track.bbox = detections[best_det]
                track.missed = 0
                assigned.add(best_det)
            else:
                track.missed += 1

        # Remove dead tracks
        self.tracks = [t for t in self.tracks if t.missed < self.max_missed]

        # Add new tracks
        for i, det in enumerate(detections):
            if i not in assigned:
                self.tracks.append(Track(det, self.next_id))
                self.next_id += 1

        return self.tracks
