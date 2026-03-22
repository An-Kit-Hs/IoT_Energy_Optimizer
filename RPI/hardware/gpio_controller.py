import RPi.GPIO as GPIO
import config

class GPIOController:
    
    def __init__(self, mqtt):
        self.mqtt = mqtt
        self.device_pins = config.DEVICE_PINS
        self.active_low = config.ACTIVE_LOW

        self.topic = "control/+/state"

        self.last_states = {d: False for d in self.device_pins}

        GPIO.setmode(GPIO.BCM)

        for pin in self.device_pins.values():
            GPIO.setup(pin, GPIO.OUT)
            self._set_output(pin, False)

    # ------------------ MQTT HANDLER ------------------

    def handle_message(self, topic, message):

        # topic: control/ac1/state
        try:
            device = topic.split("/")[1]
        except:
            return

        if device not in self.device_pins:
            return

        state = self._parse_payload(message)

        if state is None:
            print(f"[GPIO] Invalid payload for {device}: {message}")
            return

        if self.last_states[device] == state:
            return

        pin = self.device_pins[device]

        self._set_output(pin, state)

        print(f"[GPIO] {device} → {'ON' if state else 'OFF'} (GPIO {pin})")

        self.last_states[device] = state

    # ------------------ HELPERS ------------------

    def _parse_payload(self, message):
        # Supports both JSON and raw string
        try:
            if isinstance(message, dict):
                val = message.get("power", "").lower()
            else:
                val = str(message).lower()
        except:
            return None

        if val in ["on", "1", "true"]:
            return True
        elif val in ["off", "0", "false"]:
            return False

        return None

    def _set_output(self, pin, state):
        if self.active_low:
            GPIO.output(pin, GPIO.LOW if state else GPIO.HIGH)
        else:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)

    # ------------------ CLEANUP ------------------

    def cleanup(self):
        GPIO.cleanup()