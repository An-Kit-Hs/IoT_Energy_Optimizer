from mqtt import MQTTClient
from environment_system.device_manager import DeviceManager
from environment_system.controller import EnvironmentController

from occupancy import OccupancyModule
from sensors import SensorModule
from utils import EnvironmentData

from hardware import GPIOService, MQTTGPIOBridge

import config
import time

import atexit
import signal
import sys
import traceback
from datetime import datetime

# Exception logging
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def log_exit():
    log("[SYSTEM] Exiting cleanly...")


def handle_exception(exc_type, exc_value, exc_traceback):
    log("[CRASH] Unhandled exception:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)


def handle_signal(signum, frame):
    log(f"[SYSTEM] Received signal: {signum}")
    sys.exit(0)


# Register handlers
atexit.register(log_exit)
sys.excepthook = handle_exception

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# ------------------ INIT ------------------

mqtt = MQTTClient(config.MQTT_BROKER)
gpio = GPIOService()

devices = DeviceManager(mqtt)
devices.add_ac("ac1")
devices.add_ac("ac2")
devices.add_light("light1", gpio)
devices.add_exhaust("exhaust", gpio)

occupancy = OccupancyModule()
sensor = SensorModule()

controller = EnvironmentController(devices, occupancy)

gpio = GPIOService()
bridge = MQTTGPIOBridge(gpio)

people = 0

# Shared sensor cache
last_data = {
    "temperature": None,
    "humidity": None,
    "nox": None,
    "voc": None,
    "pm2_5": None,
    "co2": None
}

# ------------------ HELPERS ------------------

def build_environment():
    return EnvironmentData(
        temperature=last_data["temperature"],
        humidity=last_data["humidity"],
        nox_index=last_data["nox"],
        voc_index=last_data["voc"],
        pm2_5=last_data["pm2_5"],
        co2=last_data["co2"]
    )


def run_controller():
    data = build_environment()
    processed = sensor.update(data)

    controller.process(processed["data"], people)
    
def control_topic(device):
    return f"control/{device}/state"


# ------------------ HANDLERS ------------------

def callback(topic, message):
    state = bridge.parse_payload(message)

    parts = topic.split("/")
    device = parts[1] if len(parts) > 1 else None

    print(f"[CONTROL][MANUAL COMMAND] {device} -> {state}")

    if state is not None and device:
        controller.handle_command(device, state)
    else:
        log(f"[CONTROL] Invalid message: {message}")


def handle_sensor(topic, message):
    global last_data

    # Merge incoming data
    for key in last_data:
        if key in message:
            last_data[key] = message[key]

    run_controller()


def handle_occupancy(topic, message):
    global people

    try:
        people = message.get("count", message.get("payload", 0))
    except Exception:
        people = 0

    run_controller()


# ------------------ MQTT SETUP ------------------

mqtt.connect()
time.sleep(1)  # allow connection to settle

mqtt.subscribe(config.CONTROLS_TOPIC, callback)
mqtt.subscribe(config.SEN55_TOPIC, handle_sensor)
mqtt.subscribe(config.SCD30_TOPIC, handle_sensor)
mqtt.subscribe(config.OCC_TOPIC, handle_occupancy)

# ------------------ LOOP ------------------

try:
    while True:
        time.sleep(config.LOOP_DELAY)

except KeyboardInterrupt:
    log("[SYSTEM] Keyboard interrupt")
    gpio.cleanup()
    mqtt.disconnect()