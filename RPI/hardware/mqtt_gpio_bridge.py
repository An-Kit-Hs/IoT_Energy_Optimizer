class MQTTGPIOBridge:
    def __init__(self, gpio):
        self.gpio = gpio

    def handle_message(self, topic, message):
        try:
            device = topic.split("/")[1]
        except:
            return

        state = self._parse_payload(message)
        if state is None:
            print(f"[MQTT] Invalid payload: {message}")
            return

        try:
            self.gpio.set_device(device, state)
        except ValueError:
            print(f"[MQTT] Unknown device: {device}")

    def _parse_payload(self, message):
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