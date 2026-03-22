from utils.compressor_protection import CompressorProtection

class ACController:

    def __init__(self, mqtt, topic="home/ac/set"):
        self.mqtt = mqtt
        self.topic = topic
        self.protection = CompressorProtection()

    def turn_on(self, temp):
        if not self.protection.can_turn_on():
            return

        self.mqtt.publish(self.topic, {
            "power": "ON",
            "target_temp": temp
        })

        self.protection.mark_on()

    def turn_off(self):
        if not self.protection.can_turn_off():
            return

        self.mqtt.publish(self.topic, {
            "power": "OFF"
        })

        self.protection.mark_off()