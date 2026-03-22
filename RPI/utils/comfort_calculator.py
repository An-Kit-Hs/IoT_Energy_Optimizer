class ComfortCalculator:

    def feels_like(self, temp_c, humidity):
        temp_f = temp_c * 9/5 + 32

        hi = (
            -42.379
            + 2.04901523 * temp_f
            + 10.14333127 * humidity
            - 0.22475541 * temp_f * humidity
            - 6.83783e-3 * temp_f ** 2
            - 5.481717e-2 * humidity ** 2
            + 1.22874e-3 * temp_f ** 2 * humidity
            + 8.5282e-4 * temp_f * humidity ** 2
            - 1.99e-6 * temp_f ** 2 * humidity ** 2
        )

        return (hi - 32) * 5/9