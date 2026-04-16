# ------------------ COMFORT ------------------

COMFORT_TEMP = 24        # target temp (°C)
ECO_TEMP = 27            # energy-saving temp (°C)
TEMP_BAND = 1.5          # hysteresis band (°C)


# ------------------ MQTT ------------------

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883


# ------------------ TOPICS ------------------

SEN55_TOPIC = "sensor/data/sen55"
SCD30_TOPIC = "sensor/data/scd30"
OCC_TOPIC = "cam/occupancy"
CONTROLS_TOPIC = "control/+/state"


# ------------------ AIR QUALITY ------------------

AQI_EMERGENCY_THRESHOLD = 75
AQI_PREVENTIVE_THRESHOLD = 55

# ------------------ OCCUPANCY ------------------

EMPTY_DELAY = 120        # seconds before switching to EMPTY
MIN_ON_TIME = 10         # minimum seconds to stay ON
MIN_OFF_TIME = 10        # minimum seconds to stay OFF

# ------------------ SYSTEM ------------------

LOOP_DELAY = 0.01  # main loop delay (seconds)

# ------------------ GPIO CONFIG ------------------

ACTIVE_LOW = True

DEVICE_PINS = {
    "ac1": 17,
    "ac2": 27,
    "light1": 22,
    "exhaust": 4,
}