class ExhaustController:

    def __init__(self, mqtt, topic="home/exhaust/set"):

        self.mqtt = mqtt
        self.topic = topic
        self.state = "OFF"

    def turn_on(self):

        if self.state == "ON":
            return

        self.state = "ON"

        self.mqtt.publish(self.topic, {"power": "ON"})

    def turn_off(self):

        if self.state == "OFF":
            return

        self.state = "OFF"

        self.mqtt.publish(self.topic, {"power": "OFF"})