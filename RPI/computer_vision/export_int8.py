from ultralytics import YOLO

# Load nano model
model = YOLO("models/yolov8n.pt")

# Export with INT8 quantization
model.export(
    format="tflite",
    imgsz=320,
    int8=True,
    data="coco128.yaml"  # calibration dataset
)
