import os, warnings, logging, threading, time
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL']  = '3'
warnings.filterwarnings('ignore')
logging.getLogger('tensorflow').setLevel(logging.ERROR)

import cv2
from fer.fer import FER
from database import set_live
from config import WEBCAM_INDEX, FRAME_SKIP, USE_DIRECTSHOW, EMOTION_RISK_WEIGHTS

# FER library returns "angry" not "anger" — this maps FER keys to config keys
FER_KEY_MAP = {
    "angry":    "angry",
    "anger":    "angry",
    "disgust":  "disgust",
    "fear":     "fear",
    "happy":    "happy",
    "sad":      "sad",
    "surprise": "surprise",
    "neutral":  "neutral"
}

class EmotionEngine(threading.Thread):
    def __init__(self, session_id):
        super().__init__(daemon=True)
        self.session_id       = session_id
        self.detector         = None
        self._current_emotion = "neutral"
        self._current_score   = 0
        self._score_history   = []
        self._lock            = threading.Lock()
        self._running         = False

    def run(self):
        self._running = True
        try:
            self.detector = FER(mtcnn=True)
            print("[EmotionEngine] FER model loaded")
        except Exception as e:
            print(f"[EmotionEngine] FER load failed: {e}")
            self.detector = None

        if USE_DIRECTSHOW:
            cap = cv2.VideoCapture(WEBCAM_INDEX, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(WEBCAM_INDEX)

        if not cap.isOpened():
            print("[EmotionEngine] Webcam not available — defaulting to neutral")
            cap = None

        frame_count = 0
        while self._running:
            try:
                if cap is None or self.detector is None:
                    time.sleep(0.5)
                    set_live("emotion_current", "neutral")
                    set_live("emotion_score",    0)
                    continue

                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                frame_count += 1
                if frame_count % FRAME_SKIP != 0:
                    continue

                result = self.detector.detect_emotions(frame)
                if result:
                    emotions = result[0]["emotions"]
                    dominant = max(emotions, key=emotions.get)
                    # Fix: map FER key to config key correctly
                    mapped   = FER_KEY_MAP.get(dominant, dominant)
                    score    = EMOTION_RISK_WEIGHTS.get(mapped, 5)
                else:
                    dominant = "neutral"
                    score    = 5

                with self._lock:
                    self._current_emotion = dominant
                    self._current_score   = score
                    self._score_history.append(score)
                    if len(self._score_history) > 10:
                        self._score_history.pop(0)

                set_live("emotion_current", dominant)
                set_live("emotion_score",   score)

            except Exception as e:
                print(f"[EmotionEngine] Error: {e}")
                time.sleep(0.5)

        if cap:
            cap.release()

    def stop(self):
        self._running = False

    def reset(self):
        # Call this before PIN entry to clear old scores
        with self._lock:
            self._score_history   = []
            self._current_emotion = "neutral"
            self._current_score   = 0
        print("[EmotionEngine] Score history reset")

    def get_current(self):
        with self._lock:
            return self._current_emotion, self._current_score

    def get_averaged_score(self):
        with self._lock:
            if not self._score_history:
                return 5
            return sum(self._score_history) / len(self._score_history)