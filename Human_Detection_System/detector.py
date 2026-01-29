import numpy as np
import cv2
import tensorflow as tf

tflite = tf.lite

PERSON_CLASS_ID = 0


class HumanDetector:
    def __init__(self, model_path, conf_threshold=0.25, nms_threshold=0.45):
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        self.input_size = self.input_details[0]['shape'][1]
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold

        print("Input:", self.input_details)
        print("Output:", self.output_details)

    def detect(self, frame):
        h, w = frame.shape[:2]

        img = cv2.resize(frame, (self.input_size, self.input_size))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        input_data = np.expand_dims(img, axis=0).astype(np.float32) / 255.0

        self.interpreter.set_tensor(
            self.input_details[0]['index'], input_data
        )
        self.interpreter.invoke()

        output = self.interpreter.get_tensor(
            self.output_details[0]['index']
        )[0]                      # (84, 2100)

        output = np.transpose(output, (1, 0))  # -> (2100, 84)

        boxes = []
        scores = []

        for det in output:
            cx, cy, bw, bh = det[:4]
            class_scores = det[4:]

            class_id = np.argmax(class_scores)
            conf = class_scores[class_id]

            if conf < self.conf_threshold:
                continue

            if class_id != PERSON_CLASS_ID:
                continue

            # Scale boxes back to original image
            x = int((cx - bw / 2) * w)
            y = int((cy - bh / 2) * h)
            bw = int(bw * w)
            bh = int(bh * h)

            # Clamp to frame bounds
            x = max(0, x)
            y = max(0, y)
            bw = min(w - x, bw)
            bh = min(h - y, bh)

            boxes.append([x, y, bw, bh])
            scores.append(float(conf))

        # NMS
        indices = cv2.dnn.NMSBoxes(
            boxes,
            scores,
            self.conf_threshold,
            self.nms_threshold
        )

        detections = []
        if len(indices) > 0:
            for i in np.array(indices).flatten():
                detections.append({
                    "bbox": boxes[i],
                    "confidence": scores[i]
                })

        return detections
