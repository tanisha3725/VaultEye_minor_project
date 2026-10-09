import time, statistics
from config import (KEYSTROKE_NORMAL_MIN, KEYSTROKE_HESITATION_MS,
    KEYSTROKE_SCORE_NORMAL, KEYSTROKE_SCORE_FAST,
    KEYSTROKE_SCORE_HESITATION, KEYSTROKE_SCORE_ERRATIC)

class KeystrokeEngine:
    def __init__(self):
        self.timestamps  = []
        self.intervals   = []
        self.risk_score  = 0
        self.pattern_tag = "NORMAL"

    def record_keypress(self):
        self.timestamps.append(time.time())
        if len(self.timestamps) >= 2:
            gap_ms = (self.timestamps[-1] - self.timestamps[-2]) * 1000
            self.intervals.append(gap_ms)
            self._analyze()

    def _analyze(self):
        if not self.intervals:
            return
        avg_gap = sum(self.intervals) / len(self.intervals)
        max_gap = max(self.intervals)

        if max_gap > KEYSTROKE_HESITATION_MS:
            self.risk_score  = KEYSTROKE_SCORE_HESITATION
            self.pattern_tag = "HESITATION"
        elif avg_gap < KEYSTROKE_NORMAL_MIN:
            self.risk_score  = KEYSTROKE_SCORE_FAST
            self.pattern_tag = "TOO_FAST"
        elif len(self.intervals) >= 2:
            try:
                cv = statistics.stdev(self.intervals) / avg_gap
                if cv > 1.2:
                    self.risk_score  = KEYSTROKE_SCORE_ERRATIC
                    self.pattern_tag = "ERRATIC"
                    return
            except:
                pass
            self.risk_score  = KEYSTROKE_SCORE_NORMAL
            self.pattern_tag = "NORMAL"
        else:
            self.risk_score  = KEYSTROKE_SCORE_NORMAL
            self.pattern_tag = "NORMAL"

    def get_result(self):
        return {
            "intervals_ms": [round(i, 1) for i in self.intervals],
            "avg_gap_ms":   round(sum(self.intervals) / max(len(self.intervals), 1), 1),
            "max_gap_ms":   round(max(self.intervals, default=0), 1),
            "pattern":      self.pattern_tag,
            "risk_score":   self.risk_score,
        }

    def reset(self):
        self.timestamps  = []
        self.intervals   = []
        self.risk_score  = 0
        self.pattern_tag = "NORMAL"