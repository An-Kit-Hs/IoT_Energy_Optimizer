import time
from utils import Camera
from computer_vision_v2 import OccupancySystem
from mqtt.mqtt_client import MQTTClient
import config
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(
    BASE_DIR,
    "models",
    "yolov8n_saved_model",
    "yolov8n_int8.tflite"
)

# ------------------ CONFIG ------------------

FRAME_SKIP = 4
SLEEP_TIME = 0.02

# ------------------ INIT ------------------

mqtt = MQTTClient(config.MQTT_BROKER)
mqtt.connect()

vision = OccupancySystem(model_path)

camera = Camera(320, 240)

frame_id = 0
people = 0


# ------------------ LOOP ------------------

try:
    while True:

        # -------- Capture --------
        ret, frame = camera.read()
        if not ret:
            continue

        # -------- Detection --------
        if frame_id % FRAME_SKIP == 0:
            result = vision.process(frame)
            people = result["count"]

            mqtt.publish(
                config.OCC_TOPIC,
                {"count": people}
            )

            print(f"[VISION] People: {people}")

        frame_id += 1

        # -------- Sleep --------
        time.sleep(SLEEP_TIME)

except KeyboardInterrupt:
    print("Stopping vision service...")

finally:
    camera.release()
    mqtt.publish(config.OCC_TOPIC, {"count": 0})
    mqtt.disconnect()