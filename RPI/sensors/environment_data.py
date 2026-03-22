from dataclasses import dataclass

@dataclass
class EnvironmentData:

    temperature: float
    humidity: float
    nox_index: float
    voc_index: float
    pm2_5: float