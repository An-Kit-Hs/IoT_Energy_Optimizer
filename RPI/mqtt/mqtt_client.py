import json
import time
import threading
import paho.mqtt.client as mqtt
from typing import Callable, Optional, Dict

class MQTTClient:
    def __init__(
        self,
        broker: str,
        port: int = 1883,
        client_id: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        keepalive: int = 60,
        reconnect_delay: int = 5,
    ):
        self.broker = broker
        self.port = port
        self.keepalive = keepalive
        self.reconnect_delay = reconnect_delay

        self.client = mqtt.Client(client_id=client_id)

        if username and password:
            self.client.username_pw_set(username, password)

        # Thread safety
        self._lock = threading.Lock()

        # Topic to callback mapping
        self._callbacks: Dict[str, Callable[[str, dict], None]] = {}

        # Default fallback callback
        self._default_callback: Optional[Callable[[str, dict], None]] = None

        # Bind internal callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self._connected = False

    # ------------------ INTERNAL CALLBACKS ------------------

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT Connected")
            self._connected = True

            # Resubscribe to all topics
            for topic in self._callbacks.keys():
                self.client.subscribe(topic)

        else:
            print(f"MQTT connection failed: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print("MQTT Disconnected")
        self._connected = False

        # Auto reconnect loop
        def reconnect():
            while not self._connected:
                try:
                    print("Reconnecting...")
                    self.client.reconnect()
                    return
                except:
                    time.sleep(self.reconnect_delay)

        threading.Thread(target=reconnect, daemon=True).start()

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode()

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = payload

        # Route to specific handler
        if msg.topic in self._callbacks:
            self._callbacks[msg.topic](msg.topic, data)

        elif self._default_callback:
            self._default_callback(msg.topic, data)

        else:
            print(f"[MQTT] {msg.topic}: {data}")

    # ------------------ PUBLIC API ------------------

    def connect(self):
        self.client.connect(self.broker, self.port, self.keepalive)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic: str, callback: Callable[[str, dict], None], qos: int = 0):
        self._callbacks[topic] = callback
        self.client.subscribe(topic, qos)
        print(f"Subscribed → {topic}")

    def set_default_callback(self, callback: Callable[[str, dict], None]):
        self._default_callback = callback

    def publish(self, topic: str, message: dict, qos: int = 0, retain: bool = False):
        payload = json.dumps(message)

        with self._lock:  # thread-safe publish
            self.client.publish(topic, payload, qos=qos, retain=retain)

    def is_connected(self):
        return self._connected