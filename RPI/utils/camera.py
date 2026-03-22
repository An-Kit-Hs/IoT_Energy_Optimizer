import platform
import cv2


class Camera:

    def __init__(self, width=320, height=240, use_lores=True):
        self.system = platform.system()

        # -------- Raspberry Pi --------
        if self._is_rpi():
            from picamera2 import Picamera2  # type: ignore

            self.picam2 = Picamera2()

            if use_lores:
                config = self.picam2.create_preview_configuration(
                    main={"size": (width, height), "format": "RGB888"},
                    lores={"size": (160, 120), "format": "YUV420"}
                )
                self.stream = "lores"
            else:
                config = self.picam2.create_preview_configuration(
                    main={"size": (width, height), "format": "RGB888"}
                )
                self.stream = "main"

            self.picam2.configure(config)
            self.picam2.start()

            self.mode = "picamera"

        # -------- PC / Laptop --------
        else:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(3, width)
            self.cap.set(4, height)
            self.mode = "opencv"

    def read(self):
        if self.mode == "picamera":
            frame = self.picam2.capture_array(self.stream)

            if self.stream == "lores":
                # YUV → BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
            else:
                # RGB → BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            return True, frame

        else:
            return self.cap.read()

    def release(self):
        if self.mode == "picamera":
            self.picam2.stop()
        else:
            self.cap.release()

    def _is_rpi(self):
        try:
            with open("/proc/device-tree/model") as f:
                return "Raspberry Pi" in f.read()
        except:
            return False