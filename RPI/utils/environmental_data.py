from typing import Optional

class EnvironmentData:
    def __init__(
        self,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        nox_index: Optional[float] = None,
        voc_index: Optional[float] = None,
        pm2_5: Optional[float] = None,
        co2: Optional[float] = None
    ):
        self.temperature = temperature
        self.humidity = humidity
        self.nox_index = nox_index
        self.voc_index = voc_index
        self.pm2_5 = pm2_5
        self.co2 = co2