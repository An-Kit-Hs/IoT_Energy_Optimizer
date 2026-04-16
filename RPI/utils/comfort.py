import math

class ComfortCalculator:

    def feels_like(self, temp_c, humidity):
        """
        Exponential feels-like temperature model
        """

        try:
            # sanitize inputs
            if temp_c is None:
                return None

            if humidity is None:
                # fallback: assume neutral humidity (50%)
                humidity = 50

            temp_c = float(temp_c)
            humidity = float(humidity)

            # clamp humidity to valid range
            humidity = max(0, min(humidity, 100))

            h = humidity / 100  # normalize (0–1)

            factor = math.exp(0.05 * h * temp_c)
            feels_like = temp_c * factor

            return round(feels_like, 2)

        except Exception as e:
            print(f"[Comfort] feels_like error: {e}")
            return None