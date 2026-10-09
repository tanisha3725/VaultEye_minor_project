import tkinter as tk
from datetime import datetime
from config import *
from database import get_live, get_recent_alerts

class BackendMonitor:
    def __init__(self, root):
        self.root = root
        self._build_ui()
        self._poll()

    def _build_ui(self):
        self.root.title("VaultEye — Security Monitor [BACKEND]")
        self.root.geometry("750x800")
        self.root.configure(bg=BK_BG)

        # Red warning header
        hdr = tk.Frame(self.root, bg="#cc0000", height=45)
        hdr.pack(fill=tk.X)
        tk.Label(hdr,
                 text="  ⚠  VAULTEYE SECURITY MONITOR  —  RESTRICTED ACCESS  ⚠",
                 bg="#cc0000", fg="white",
                 font=("Courier", 12, "bold")).pack(pady=10)

        # Session info row
        info = tk.Frame(self.root, bg=BK_PANEL, pady=8)
        info.pack(fill=tk.X, padx=10, pady=(8,0))
        self.lbl_session = tk.Label(info, text="Session: ---",
                                    bg=BK_PANEL, fg=CLR_INFO,
                                    font=("Courier", 11))
        self.lbl_session.pack(side=tk.LEFT, padx=15)
        self.lbl_stage = tk.Label(info, text="Stage: WAITING",
                                  bg=BK_PANEL, fg=CLR_WARN,
                                  font=("Courier", 11, "bold"))
        self.lbl_stage.pack(side=tk.RIGHT, padx=15)

        # Metric cards
        cards = tk.Frame(self.root, bg=BK_BG)
        cards.pack(fill=tk.X, padx=10, pady=10)
        self.card_emo = self._make_card(cards, "EMOTION",   "neutral", CLR_SAFE)
        self.card_ks  = self._make_card(cards, "KEYSTROKE", "NORMAL",  CLR_SAFE)
        self.card_pin = self._make_card(cards, "PIN TYPE",  "---",     CLR_INFO)
        for c in [self.card_emo, self.card_ks, self.card_pin]:
            c.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Risk gauge
        gf = tk.Frame(self.root, bg=BK_PANEL, pady=12)
        gf.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(gf, text="FUSION RISK SCORE",
                 bg=BK_PANEL, fg=CLR_INFO,
                 font=("Courier", 13, "bold")).pack()
        self.gauge = tk.Canvas(gf, width=700, height=38,
                               bg="#222222", highlightthickness=0)
        self.gauge.pack(padx=20, pady=6)
        self.lbl_score = tk.Label(gf,
                                  text="Score: 0 / 100  |  Level: LOW",
                                  bg=BK_PANEL, fg=CLR_SAFE,
                                  font=("Courier", 14, "bold"))
        self.lbl_score.pack()

        # Alert banner
        self.banner = tk.Label(self.root,
                               text="  SYSTEM NOMINAL — NO THREATS DETECTED",
                               bg=BK_PANEL, fg=CLR_SAFE,
                               font=("Courier", 13, "bold"),
                               pady=12, anchor=tk.W)
        self.banner.pack(fill=tk.X, padx=10, pady=5)

        # Breakdown box
        bf = tk.Frame(self.root, bg=BK_PANEL, pady=8)
        bf.pack(fill=tk.X, padx=10)
        tk.Label(bf, text="SCORE BREAKDOWN",
                 bg=BK_PANEL, fg=CLR_INFO,
                 font=("Courier", 11, "bold")).pack(anchor=tk.W, padx=12)
        self.breakdown_box = tk.Text(bf, height=5, bg="#111111",
                                     fg=CLR_SAFE,
                                     font=("Courier", 10),
                                     relief=tk.FLAT,
                                     state=tk.DISABLED)
        self.breakdown_box.pack(fill=tk.X, padx=12, pady=4)

        # Alert log
        lf = tk.Frame(self.root, bg=BK_PANEL, pady=8)
        lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tk.Label(lf, text="ALERT LOG",
                 bg=BK_PANEL, fg=CLR_INFO,
                 font=("Courier", 11, "bold")).pack(anchor=tk.W, padx=12)
        self.log_box = tk.Text(lf, height=10, bg="#0a0a0a",
                               fg=CLR_WARN,
                               font=("Courier", 9),
                               relief=tk.FLAT,
                               state=tk.DISABLED)
        sb = tk.Scrollbar(lf, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,12))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        # Footer
        tk.Label(self.root,
                 text="VaultEye v1.0  |  GNDEC Ludhiana  |  CSE Minor Project 2026",
                 bg=BK_BG, fg="#444444",
                 font=("Courier", 9)).pack(pady=5)

    def _make_card(self, parent, title, value, color):
        f = tk.Frame(parent, bg=BK_PANEL, pady=8)
        tk.Label(f, text=title, bg=BK_PANEL, fg="#888888",
                 font=("Courier", 9, "bold")).pack()
        lbl = tk.Label(f, text=value, bg=BK_PANEL, fg=color,
                       font=("Courier", 13, "bold"))
        lbl.pack()
        f._value_label = lbl
        return f

    def _draw_gauge(self, score, color):
        self.gauge.delete("all")
        self.gauge.create_rectangle(0, 0, 700, 38,
                                    fill="#222222", outline="")
        # Zone backgrounds
        self.gauge.create_rectangle(0,   0, 210, 38, fill="#003300", outline="")
        self.gauge.create_rectangle(210, 0, 385, 38, fill="#333300", outline="")
        self.gauge.create_rectangle(385, 0, 700, 38, fill="#330000", outline="")
        # Score bar
        width = int((score / 100) * 700)
        if width > 0:
            self.gauge.create_rectangle(0, 4, width, 34,
                                        fill=color, outline="")
        # Labels
        for x, txt in [(105,"LOW"),(297,"MEDIUM"),(542,"CRITICAL")]:
            self.gauge.create_text(x, 19, text=txt,
                                   fill="white",
                                   font=("Courier", 9, "bold"))

    def _poll(self):
        try:
            self._refresh()
        except Exception as e:
            print(f"[Monitor] Error: {e}")
        self.root.after(500, self._poll)

    def _refresh(self):
        # Session
        sid   = get_live("session_id", "---")
        stage = get_live("atm_stage",  "WAITING")
        self.lbl_session.config(text=f"Session: {sid}")
        self.lbl_stage.config(text=f"Stage: {stage.upper()}")

        # Emotion card
        emotion   = get_live("emotion_current", "neutral")
        emo_score = get_live("emotion_score",   0)
        emo_color = self._emotion_color(emotion)
        self.card_emo._value_label.config(
            text=f"{emotion.upper()}\n({emo_score:.0f})",
            fg=emo_color)

        # Keystroke card — safely handle corrupted/string data
        ks = get_live("last_ks_result", {})
        if isinstance(ks, str):
            ks = {}
        ks_pattern = ks.get("pattern",    "---") if ks else "---"
        ks_score   = ks.get("risk_score", 0)     if ks else 0
        ks_color   = CLR_SAFE if ks_score < 30 else \
                     CLR_WARN if ks_score < 60 else CLR_DANGER
        self.card_ks._value_label.config(
            text=f"{ks_pattern}\n({ks_score})",
            fg=ks_color)

        # PIN card
        pin_lbl   = get_live("pin_submitted", "---")
        pin_color = CLR_DANGER if pin_lbl == "DURESS_PIN" else \
                    CLR_WARN   if pin_lbl == "WRONG_PIN"  else CLR_SAFE
        self.card_pin._value_label.config(text=pin_lbl, fg=pin_color)

        # Risk gauge
        score = get_live("risk_score", 0)
        level = get_live("risk_level", "LOW")
        lc    = self._level_color(level)
        self._draw_gauge(score, lc)
        self.lbl_score.config(
            text=f"Score: {score:.1f} / 100  |  Level: {level}",
            fg=lc)

        # Banner
        is_duress = get_live("is_duress", False)
        if is_duress:
            self.banner.config(
                text="  🚨 DURESS PIN DETECTED — SILENT ALERT — POLICE NOTIFIED 🚨",
                bg=CLR_DANGER, fg="white")
        elif level == "HIGH":
            self.banner.config(
                text="  ⚠  SUSPICIOUS ACTIVITY DETECTED — MONITORING CLOSELY  ⚠",
                bg=CLR_WARN, fg="black")
        elif level == "MEDIUM":
            self.banner.config(
                text="  ⚠  ELEVATED RISK — WATCHING TRANSACTION",
                bg="#664400", fg="white")
        else:
            self.banner.config(
                text="  SYSTEM NOMINAL — NO THREATS DETECTED",
                bg=BK_PANEL, fg=CLR_SAFE)

        # Breakdown
        bd = get_live("risk_breakdown", {})
        if bd:
            self.breakdown_box.config(state=tk.NORMAL)
            self.breakdown_box.delete("1.0", tk.END)
            self.breakdown_box.insert(tk.END,
                f"  Emotion Score   : {bd.get('emotion_score',0)}\n"
                f"  Keystroke Score : {bd.get('keystroke_score',0)}"
                f"  ({bd.get('keystroke_pattern','---')})\n"
                f"  PIN Type        : {bd.get('pin_label','---')}\n"
                f"  Final Score     : {bd.get('final_score',0)}\n"
                f"  Action          : {bd.get('action','---')}")
            self.breakdown_box.config(state=tk.DISABLED)

        # Alert log
        alerts = get_recent_alerts(15)
        self.log_box.config(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        for ts, atype, msg, sev in alerts:
            time_str = ts[11:19]
            self.log_box.insert(tk.END,
                f"[{time_str}] [{sev:<8}] {atype:<20} {msg}\n")
        self.log_box.config(state=tk.DISABLED)

    def _emotion_color(self, emotion):
        high_risk = ["angry", "fear", "disgust"]
        mid_risk  = ["sad", "surprise"]
        if emotion in high_risk:
            return CLR_DANGER
        elif emotion in mid_risk:
            return CLR_WARN
        return CLR_SAFE

    def _level_color(self, level):
        return {
            "LOW":      CLR_SAFE,
            "MEDIUM":   CLR_WARN,
            "HIGH":     CLR_DANGER,
            "CRITICAL": CLR_DANGER,
        }.get(level, CLR_SAFE)