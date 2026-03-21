from utils.moving_average import MovingAverage


class SensorSmoother:

    def __init__(self):

        self.temp = MovingAverage()
        self.humidity = MovingAverage()
        self.nox = MovingAverage()
        self.voc = MovingAverage()
        self.pm25 = MovingAverage()

    def smooth(self, data):

        data.temperature = self.temp.update(data.temperature)
        data.humidity = self.humidity.update(data.humidity)
        data.nox_index = self.nox.update(data.nox_index)
        data.voc_index = self.voc.update(data.voc_index)
        data.pm2_5 = self.pm25.update(data.pm2_5)

        return data