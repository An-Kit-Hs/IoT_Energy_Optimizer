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
devices.add_light("light1")
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

    if state != None:
        gpio.set_device(device, state=state)

    else: 
        print("GPIO prasing error")

last_data = {
    "temperature": None,
    "humidity": None,
    "nox": None,
    "voc": None,
    "pm2_5": None,
    "co2": None
}

def handle_sensor(topic, message):
    global last_data

    # Merge new values
    for key in last_data:
        if key in message:
            last_data[key] = message[key]

    data = EnvironmentData(
        temperature=last_data["temperature"],
        humidity=last_data["humidity"],
        nox_index=last_data["nox"],
        voc_index=last_data["voc"],
        pm2_5=last_data["pm2_5"],
        co2=last_data["co2"]
    )

    processed = sensor.update(data)
    controller.process(processed["data"], people)


def handle_occupancy(topic, message):
    global people

    try:
        people = message.get("count", message.get("payload", 0))
    except Exception:
        people = 0


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
    mqtt.disconnect()