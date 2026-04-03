from mqtt import MQTTClient
from environment_system.device_manager import DeviceManager
from environment_system.controller import EnvironmentController

from occupancy import OccupancyModule
from sensors import SensorModule
from utils import EnvironmentData

from hardware import GPIOService, MQTTGPIOBridge

import config
import time

# ------------------ INIT ------------------

mqtt = MQTTClient(config.MQTT_BROKER)

# Devices
devices = DeviceManager(mqtt)
devices.add_ac("ac1")
devices.add_ac("ac2")
devices.add_exhaust("exhaust")

# Modules
occupancy = OccupancyModule()
sensor = SensorModule()

# Controller
controller = EnvironmentController(devices, occupancy)

gpio = GPIOService()
bridge = MQTTGPIOBridge(gpio)

# Shared state
people = 0


# ------------------ HANDLERS ------------------

def callback(topic, message):
    state = bridge.parse_payload(message)
    device = topic.split("/")[1]

    print(f"[CONTROL] {device} -> {state}")

    if state:
        gpio.set_device(device, state=state)

    else: 
        print("GPIO prasing error")



def handle_sensor(topic, message):
    global people

    try:
        data = EnvironmentData(
            temperature=message["temperature"],
            humidity=message["humidity"],
            nox_index=message["nox"],
            voc_index=message["voc"],
            pm2_5=message["pm2_5"]
        )
    except KeyError:
        print("[ERROR] Invalid sensor payload:", message)
        return

    # -------- Sensor processing --------
    processed = sensor.update(data)
    data = processed["data"]

    # -------- Control --------
    controller.process(data, people)


def handle_occupancy(topic, message):
    global people

    try:
        people = message.get("count", message.get("payload", 0))
    except Exception:
        people = 0

    # Debug
    print(f"[OCCUPANCY] People: {people}")


# ------------------ MQTT SETUP ------------------

mqtt.connect()

mqtt.subscribe(config.CONTROLS_TOPIC, callback)
mqtt.subscribe(config.SEN55_TOPIC, handle_sensor)
mqtt.subscribe(config.OCC_TOPIC, handle_occupancy)
mqtt.subscribe(config.SCD30_TOPIC, handle_sensor)


# ------------------ MAIN LOOP ------------------

try:
    while True:
        time.sleep(config.LOOP_DELAY)

except KeyboardInterrupt:
    print("Shutting down...")
    occupancy.save()
    mqtt.disconnect()