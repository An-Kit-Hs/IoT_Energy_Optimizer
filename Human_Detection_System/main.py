import cv2
import numpy as np
from detector import HumanDetector
from utils import draw_boxes, draw_info_panel, FPSCounter, OccupancyMap
from sort_tracker import SortTracker

MODEL_PATH = "models/yolov8n_saved_model/yolov8n_int8.tflite"

MAP_SCALE_X = 0.3
MAP_SCALE_Y = 0.3

def bbox_to_map_point(bbox):
    x, y, w, h = bbox
    cx = x + w / 2
    cy = y + h / 2

    px = int(cx * MAP_SCALE_X)
    py = int(cy * MAP_SCALE_Y)

    return px, py

def main():
    cv2.setUseOptimized(True)
    cv2.setNumThreads(2)

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    detector = HumanDetector(MODEL_PATH, conf_threshold=0.4)
    tracker = SortTracker(max_missed=7, iou_threshold=0.3)

    fps_counter = FPSCounter()
    occupancy = OccupancyMap(200, 200)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        detections = detector.detect(frame)

        # Convert detections to bbox list
        det_boxes = [d["bbox"] for d in detections]

        # Update tracker
        tracks = tracker.update(det_boxes)

        # Update occupancy using tracked boxes
        points = []
        for t in tracks:
            p = bbox_to_map_point(t.bbox)
            points.append(p)

        occupancy.update(points)

        # Draw camera view
        cam_view = frame.copy()
        cam_view = draw_boxes(cam_view, tracks)

        fps = fps_counter.update()
        cam_view = draw_info_panel(cam_view, fps, len(tracks))

        map_view = occupancy.render(size=(320,240))
        cam_view = cv2.resize(cam_view, (320,240))

        ui = np.hstack((cam_view, map_view))

        cv2.imshow("Human Detection + Tracking (RPi4)", ui)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
