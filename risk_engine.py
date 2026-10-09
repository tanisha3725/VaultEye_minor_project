import os
import warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL']  = '3'
warnings.filterwarnings('ignore')

from config import (NORMAL_PIN, DURESS_PIN_SCORE,
    WEIGHT_EMOTION, WEIGHT_KEYSTROKE, WEIGHT_PIN,
    RISK_THRESHOLD_LOW, RISK_THRESHOLD_MEDIUM, RISK_THRESHOLD_HIGH)
from database import set_live, log_event, log_alert

def _compute_duress_pin(normal_pin):
    # Duress PIN = each digit +1 (9 wraps to 0)
    return "".join(str((int(d) + 1) % 10) for d in normal_pin)

DURESS_PIN = _compute_duress_pin(NORMAL_PIN)

class RiskEngine:
    def __init__(self, session_id):
        self.session_id  = session_id
        self.final_score = 0.0
        self.risk_level  = "LOW"
        self.is_duress   = False
        self.breakdown   = {}

    def evaluate(self, entered_pin, emotion_score,
                 keystroke_score, keystroke_pattern):

        self.is_duress = False

        # PIN scoring
        if entered_pin == DURESS_PIN:
            pin_score      = DURESS_PIN_SCORE
            self.is_duress = True
            pin_label      = "DURESS_PIN"
        elif entered_pin == NORMAL_PIN:
            pin_score  = 0
            pin_label  = "NORMAL_PIN"
        else:
            pin_score  = 60
            pin_label  = "WRONG_PIN"

        # Weighted fusion
        w_emo = emotion_score   * WEIGHT_EMOTION
        w_ks  = keystroke_score * WEIGHT_KEYSTROKE
        w_pin = pin_score       * WEIGHT_PIN

        self.final_score = min(100.0, max(0.0, w_emo + w_ks + w_pin))

        # Risk level
        if self.is_duress or self.final_score >= RISK_THRESHOLD_HIGH:
            self.risk_level = "CRITICAL"
        elif self.final_score >= RISK_THRESHOLD_MEDIUM:
            self.risk_level = "HIGH"
        elif self.final_score >= RISK_THRESHOLD_LOW:
            self.risk_level = "MEDIUM"
        else:
            self.risk_level = "LOW"

        # Action
        if self.is_duress:
            action = "ALERT_SILENT"
        elif self.risk_level == "HIGH":
            action = "ALERT_WATCHLIST"
        elif pin_label == "WRONG_PIN":
            action = "WRONG_PIN"
        else:
            action = "ALLOW"

        self.breakdown = {
            "emotion_score":     round(emotion_score, 2),
            "keystroke_score":   round(keystroke_score, 2),
            "keystroke_pattern": keystroke_pattern,
            "pin_label":         pin_label,
            "final_score":       round(self.final_score, 2),
            "risk_level":        self.risk_level,
            "is_duress":         self.is_duress,
            "action":            action,
        }

        set_live("risk_score",     round(self.final_score, 2))
        set_live("risk_level",     self.risk_level)
        set_live("risk_breakdown", self.breakdown)
        set_live("is_duress",      self.is_duress)

        log_event(self.session_id, "RISK_EVALUATED",
                  self.breakdown, self.final_score)

        if self.is_duress:
            msg = "DURESS PIN detected — SILENT ALERT TRIGGERED"
            sev = "CRITICAL"
        elif pin_label == "WRONG_PIN":
            msg = "Wrong PIN entered — access denied"
            sev = "MEDIUM"
        elif action == "ALERT_WATCHLIST":
            msg = "Suspicious behavior detected — added to watchlist"
            sev = "HIGH"
        else:
            msg = "Normal transaction completed"
            sev = "LOW"

        log_alert(self.session_id, action, msg, sev)

        return self.breakdown