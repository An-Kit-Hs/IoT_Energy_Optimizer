import json
import paho.mqtt.client as mqtt
from typing import Callable, Optional


class MQTTClient:
    def __init__(
        self,
        broker: str,
        port: int = 1883,
        client_id: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        keepalive: int = 60,
    ):
        self.broker = broker
        self.port = port
        self.keepalive = keepalive

        self.client = mqtt.Client(client_id=client_id)

        if username and password:
            self.client.username_pw_set(username, password)

        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self._message_callback: Optional[Callable[[str, dict], None]] = None

    # Callbacks
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker")
        else:
            print(f"Failed to connect, return code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT Broker")

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = payload

        print(f"Message received on {msg.topic}: {data}")

        if self._message_callback:
            self._message_callback(msg.topic, data)

    # Methods
    def connect(self):
        self.client.connect(self.broker, self.port, self.keepalive)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic: str, qos: int = 0):
        self.client.subscribe(topic, qos)
        print(f"Subscribed to topic: {topic}")

    def publish(self, topic: str, message: dict, qos: int = 0, retain: bool = False):
        payload = json.dumps(message)
        self.client.publish(topic, payload, qos=qos, retain=retain)
        print(f"Published to {topic}: {message}")

    def set_message_callback(self, callback: Callable[[str, dict], None]):
        """
        callback(topic, message_dict)
        """
        self._message_callback = callback
