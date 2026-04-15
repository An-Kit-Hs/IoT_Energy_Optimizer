class BaseDevice:
    def __init__(self, mqtt, topic):
        self.mqtt = mqtt
        self.topic = topic
        self.state = "OFF"

    def publish(self, payload, topic=None):
        target_topic = topic if topic else self.topic
        print(f"[MQTT] {target_topic} -> {payload}")
        self.mqtt.publish(target_topic, payload)