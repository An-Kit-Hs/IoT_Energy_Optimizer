class AQIScorer:

    def _safe(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def score_pm25(self, pm):
        pm = self._safe(pm)
        if pm is None:
            return None

        if pm < 12:
            return 0
        if pm < 35:
            return 25
        if pm < 55:
            return 50
        return 100

    def score_voc(self, voc):
        voc = self._safe(voc)
        if voc is None:
            return None
        return min(voc / 5, 100)

    def score_nox(self, nox):
        nox = self._safe(nox)
        if nox is None:
            return None
        return min(nox / 5, 100)

    def score_co2(self, co2):
        co2 = self._safe(co2)
        if co2 is None:
            return None

        if co2 < 600:
            return 0
        if co2 < 1000:
            return 25
        if co2 < 1500:
            return 50
        return 100

    def overall(self, data):
        scores = {
            "pm": self.score_pm25(data.pm2_5),
            "voc": self.score_voc(data.voc_index),
            "nox": self.score_nox(data.nox_index),
            "co2": self.score_co2(data.co2),
        }

        weights = {
            "pm": 0.4,
            "voc": 0.25,
            "nox": 0.15,
            "co2": 0.2,
        }

        # keep only valid scores
        valid = {k: v for k, v in scores.items() if v is not None}

        if not valid:
            return None  # nothing usable

        # normalize weights (important if some values missing)
        total_weight = sum(weights[k] for k in valid)

        return sum(valid[k] * weights[k] for k in valid) / total_weight