class IAQScorer:

    def _safe(self, v):
        try:
            return float(v)
        except:
            return None

    def _scale(self, x, good, bad):
        # smooth 0 → 100 scaling
        if x <= good:
            return 0
        if x >= bad:
            return 100
        return (x - good) / (bad - good) * 100

    def score_pm25(self, pm):
        pm = self._safe(pm)
        if pm is None:
            return None
        return self._scale(pm, 5, 50)   # indoor thresholds

    def score_voc(self, voc):
        voc = self._safe(voc)
        if voc is None:
            return None
        return self._scale(voc, 50, 300)   # typical VOC index range

    def score_nox(self, nox):
        nox = self._safe(nox)
        if nox is None:
            return None
        return self._scale(nox, 20, 200)

    def score_co2(self, co2):
        co2 = self._safe(co2)
        if co2 is None:
            return None
        return self._scale(co2, 500, 2000)

    def overall(self, data):
        scores = {
            "pm": self.score_pm25(data.pm2_5),
            "voc": self.score_voc(data.voc_index),
            "nox": self.score_nox(data.nox_index),
            "co2": self.score_co2(data.co2),
        }

        weights = {
            "pm": 0.35,
            "voc": 0.25,
            "nox": 0.15,
            "co2": 0.25,
        }

        valid = {k: v for k, v in scores.items() if v is not None}
        if not valid:
            return None

        total_w = sum(weights[k] for k in valid)
        return sum(valid[k] * weights[k] for k in valid) / total_w