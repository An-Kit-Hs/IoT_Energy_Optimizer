import math

class ComfortCalculator:


    def feels_like(self, temp_c, humidity):
        """
        Exponential feels-like temperature model
        temp_c: temperature in Celsius
        humidity: relative humidity (0–100)
        """

        h = humidity / 100  # normalize (0–1)

        # exponential scaling factor
        factor = math.exp(0.05 * h * temp_c)

        feels_like = temp_c * factor

        return round(feels_like, 2)