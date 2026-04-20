class MQTTGPIOBridge:
    def __init__(self, gpio):
        self.gpio = gpio

    def handle_message(self, topic, message):
        try:
            device = topic.split("/")[1]
        except:
            return

        state = self.parse_payload(message)

        print(f"[MQTT] {device} -> {state}")

        if state is None:
            print(f"[MQTT] Invalid payload: {message}")
            return

        try:
            # GPIO only cares about power
            if isinstance(state, dict):
                power = state.get("power")
                if power is None:
                    print(f"[MQTT] No power field for {device}")
                    return

                value = power in ["on", "1", "true"]
            else:
                value = bool(state)

            self.gpio.set_device(device, value)

        except ValueError:
            print(f"[MQTT] Unknown device: {device}")

    def parse_payload(self, message):
        try:
            # If already dict → normalize
            if isinstance(message, dict):
                data = message.copy()

            else:
                import json

                # Try JSON decode first
                try:
                    data = json.loads(message)
                except Exception:
                    # fallback: simple string
                    val = str(message).lower()
                    if val in ["on", "1", "true"]:
                        return {"power": "on"}
                    elif val in ["off", "0", "false"]:
                        return {"power": "off"}
                    return None

            # Normalize power field if exists
            if "power" in data:
                data["power"] = str(data["power"]).lower()

            return data

        except Exception:
            return None