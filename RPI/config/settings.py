# ------------------ COMFORT ------------------

COMFORT_TEMP = 24        # target temp (°C)
ECO_TEMP = 27            # energy-saving temp (°C)
TEMP_BAND = 1.5          # hysteresis band (°C)


# ------------------ MQTT ------------------

MQTT_BROKER = "localhost"
MQTT_PORT = 1883


# ------------------ TOPICS ------------------

SEN55_TOPIC = "sensors/data/sen55"
SCD30_TOPIC = "sensors/data/scd30"
OCC_TOPIC = "cam/occupancy"


# ------------------ AIR QUALITY ------------------

AQI_EMERGENCY_THRESHOLD = 75
AQI_PREVENTIVE_THRESHOLD = 55


# ------------------ SYSTEM ------------------

LOOP_DELAY = 0.01  # main loop delay (seconds)

# ------------------ GPIO CONFIG ------------------

ACTIVE_LOW = True

DEVICE_PINS = {
    "ac1": 17,
    "ac2": 27,
    "light": 22,
    "exhaust": 4,
}