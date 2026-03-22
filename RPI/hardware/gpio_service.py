import time
from mqtt import MQTTClient
from hardware.gpio_controller import GPIOController
import config

mqtt = MQTTClient(config.MQTT_BROKER)
gpio = GPIOController(mqtt)

def callback(topic, message):
    gpio.handle_message(topic, message)

mqtt.connect()
mqtt.subscribe("control/+/state", callback)

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Stopping GPIO service...")

finally:
    gpio.cleanup()
    mqtt.disconnect()