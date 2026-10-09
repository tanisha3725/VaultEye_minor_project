# ============================================================
# VaultEye — Configuration File
# ============================================================

NORMAL_PIN = "1234"
PIN_LENGTH = 4

RISK_THRESHOLD_LOW    = 30
RISK_THRESHOLD_MEDIUM = 55
RISK_THRESHOLD_HIGH   = 80

EMOTION_WEIGHTS = {
    "fear":     90,
    "angry":    70,
    "disgust":  65,
    "sad":      50,
    "surprise": 40,
    "happy":    5,
    "neutral":  5
}

KEYSTROKE_NORMAL_MIN       = 150
KEYSTROKE_NORMAL_MAX       = 1200
KEYSTROKE_HESITATION       = 2500
KEYSTROKE_HESITATION_MS    = 2500
KEYSTROKE_SCORE_NORMAL     = 5
KEYSTROKE_SCORE_FAST       = 40
KEYSTROKE_SCORE_HESITATION = 65
KEYSTROKE_SCORE_ERRATIC    = 50

DURESS_PIN_SCORE = 100

WEIGHT_EMOTION   = 0.40
WEIGHT_KEYSTROKE = 0.25
WEIGHT_PIN       = 0.35

DB_PATH           = "vaulteye_data.db"
WEBCAM_INDEX      = 0
FRAME_SKIP        = 3
USE_DIRECTSHOW    = True

ATM_BG_COLOR     = "#1a1a2e"
ATM_ACCENT_COLOR = "#16213e"
ATM_BTN_COLOR    = "#0f3460"
ATM_TEXT_COLOR   = "#e0e0e0"
ATM_GREEN        = "#00b894"
ATM_RED          = "#d63031"
ATM_YELLOW       = "#fdcb6e"

BG_DARK    = "#0d0d0d"
BG_PANEL   = "#1a1a1a"
CLR_SAFE   = "#00ff88"
CLR_WARN   = "#ffaa00"
CLR_DANGER = "#ff3333"
CLR_INFO   = "#00aaff"

TRANSACTION_AMOUNT = 5000
BK_BG       = "#0d0d0d"
BK_PANEL    = "#1a1a1a"
BK_SAFE     = "#00ff88"
BK_WARN     = "#ffaa00"
BK_DANGER   = "#ff3333"
BK_INFO     = "#00aaff"
EMOTION_RISK_WEIGHTS = EMOTION_WEIGHTS