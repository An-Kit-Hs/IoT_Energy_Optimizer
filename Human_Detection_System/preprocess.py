import cv2
import numpy as np

def preprocess_frame(frame, size=(320, 320)):
    """
    Resize and prepare frame for MobileNet SSD
    """
    blob = cv2.dnn.blobFromImage(
        frame,
        scalefactor=0.007843,
        size=size,
        mean=(127.5, 127.5, 127.5),
        swapRB=False,
        crop=False
    )
    return blob
