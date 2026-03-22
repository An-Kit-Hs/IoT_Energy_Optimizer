import cv2
import numpy as np

def preprocess_frame(frame, size=(320,320)):
    img = cv2.resize(frame, size)
    img = img[..., ::-1]   # BGR to RGB
    img = img.astype(np.float32)
    img *= 1/255.0
    return img[None]
