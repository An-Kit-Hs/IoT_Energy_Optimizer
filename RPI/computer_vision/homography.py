import numpy as np
import cv2

class HomographyMapper:
    def __init__(self, cam_points=None, map_points=None, H=None):
        """
        Initialize with either:
        - cam_points & map_points
        OR
        - H directly (load from file)
        """

        if H is not None:
            self.H = np.array(H, dtype=np.float32)

        elif cam_points is not None and map_points is not None:
            cam_pts = np.array(cam_points, dtype=np.float32)
            map_pts = np.array(map_points, dtype=np.float32)

            self.H, _ = cv2.findHomography(cam_pts, map_pts)

            if self.H is None:
                raise ValueError("Could not compute homography.")

        else:
            raise ValueError("Provide either H or (cam_points & map_points)")

    def bbox_to_map_point(self, bbox, use_feet=True):
        x, y, w, h = bbox
        cx = x + w/2
        cy = y + h if use_feet else y + h/2

        pt = np.array([cx, cy, 1.0])
        mapped = self.H @ pt
        mapped /= mapped[2]

        return int(mapped[0]), int(mapped[1])


    def draw_roi(self, frame, cam_points, color=(255,0,0), thickness=2):
        pts = np.array(cam_points, dtype=int)
        cv2.polylines(frame, [pts], True, color, thickness)
        return frame

    def save(self, path="homography.npy"):
        np.save(path, self.H)

    @staticmethod
    def load(path="homography.npy"):
        H = np.load(path)
        return HomographyMapper(H=H)
