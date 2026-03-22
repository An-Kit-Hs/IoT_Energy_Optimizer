from mqtt.mqtt_client import MQTTClient
from controllers.ac_controller import ACController
from controllers.exhaust_controller import ExhaustController
from controllers.environment_controller import EnvironmentController
from occupancy.occupancy_controller import OccupancyController
from sensors.environment_data import EnvironmentData
import config

mqtt = MQTTClient(config.MQTT_BROKER)

ac = ACController(mqtt)
exhaust = ExhaustController(mqtt)
occupancy = OccupancyController()

controller = EnvironmentController(ac, exhaust, occupancy)
people = 0

def callback(topic, message):
    global people

    if topic == config.SEN55_TOPIC:
        data = EnvironmentData(
            temperature=message["temperature"],
            humidity=message["humidity"],
            nox_index=message["nox"],
            voc_index=message["voc"],
            pm2_5=message["pm2_5"]
        )

        controller.process(data, people)

    elif topic == config.OCC_TOPIC:
        people = message["payload"]


mqtt.set_message_callback(callback)
mqtt.connect()
mqtt.subscribe(config.SEN55_TOPIC)
mqtt.subscribe(config.SCD30_TOPIC)
mqtt.subscribe(config.OCC_TOPIC)

while True:
    pass