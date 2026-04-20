import json

def _lowercase_payload(data):
    if isinstance(data, dict):
        return {k: _lowercase_payload(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_lowercase_payload(i) for i in data]
    elif isinstance(data, str):
        return data.lower()
    else:
        return data

class BaseDevice:
    def __init__(self, mqtt, topic):
        self.mqtt = mqtt
        self.topic = topic
        self.state = "OFF"

    def publish(self, payload, topic=None):
        
        # If it's already a string then send as-is
        if isinstance(payload, str):
            final_payload = payload.lower()
            
        # If it's dict/list then serialize
        elif isinstance(payload, (dict, list)):
            payload = _lowercase_payload(payload)
            final_payload = json.dumps(payload)

        else:
            raise ValueError("Unsupported payload type")

        if topic is None:
            topic = self.topic

        print(f"[MQTT] {topic} -> {final_payload}")
        self.mqtt.publish(topic, final_payload)