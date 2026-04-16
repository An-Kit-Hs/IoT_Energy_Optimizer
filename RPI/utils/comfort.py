import math

class ComfortCalculator:

    def feels_like(self, temp_c, humidity):
        """
        Returns perceived temperature in °C
        Uses heat index for warm conditions
        Falls back to actual temperature for normal/cool conditions
        """

        if temp_c is None or humidity is None:
            return None

        # Clamp humidity to safe range
        humidity = max(0, min(100, humidity))

        # Actual temp if conditions don't need heat index
        if temp_c < 27:
            return round(temp_c, 1)

        # Convert Celsius → Fahrenheit
        T = temp_c * 9 / 5 + 32
        R = humidity

        # NOAA Heat Index Formula
        HI = (
            -42.379
            + 2.04901523 * T
            + 10.14333127 * R
            - 0.22475541 * T * R
            - 0.00683783 * T * T
            - 0.05481717 * R * R
            + 0.00122874 * T * T * R
            + 0.00085282 * T * R * R
            - 0.00000199 * T * T * R * R
        )

        # Convert back to Celsius
        feels_c = (HI - 32) * 5 / 9

        # Feels-like shouldn't exceed +10°C above actual in normal indoor conditions
        feels_c = min(feels_c, temp_c + 10)
        feels_c = 0.7 * feels_c + 0.3 * temp_c

        return round(feels_c, 1)