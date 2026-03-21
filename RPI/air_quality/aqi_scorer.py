class AQIScorer:

    def score_pm25(self, pm):

        if pm < 12:
            return 0
        if pm < 35:
            return 25
        if pm < 55:
            return 50

        return 100

    def score_voc(self, voc):
        return min(voc / 5, 100)

    def score_nox(self, nox):
        return min(nox / 5, 100)

    def overall(self, data):

        pm = self.score_pm25(data.pm2_5)
        voc = self.score_voc(data.voc_index)
        nox = self.score_nox(data.nox_index)

        return pm * 0.5 + voc * 0.3 + nox * 0.2