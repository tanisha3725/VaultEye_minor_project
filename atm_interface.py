import os
import warnings
import logging
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL']  = '3'
warnings.filterwarnings('ignore')
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('keras').setLevel(logging.ERROR)

import tkinter as tk
import uuid
import threading
from datetime import datetime

from config import *
from database import init_db, create_session, set_live, get_live
from emotion_engine import EmotionEngine
from keystroke_engine import KeystrokeEngine
from risk_engine import RiskEngine
from otp_service import generate_otp, send_otp, verify_otp

ATM_BG    = ATM_BG_COLOR
ATM_PANEL = ATM_ACCENT_COLOR
ATM_BTN   = ATM_BTN_COLOR
ATM_TEXT  = ATM_TEXT_COLOR
ATM_BLUE  = "#2196F3"

MOBILE_ACCOUNTS = {
    "9000000001": {"name": "DEMO USER 1", "account": "XXXX-XXXX-1234", "balance": 85000},
    "9000000002": {"name": "DEMO USER 2",  "account": "XXXX-XXXX-5678", "balance": 530500},
    "9000000003": {"name": "DEMO USER 3",  "account": "XXXX-XXXX-9012", "balance": 120000},
}

class ATMInterface:

    def __init__(self, root):
        self.root = root
        self.session_id   = str(uuid.uuid4())[:8].upper()
        self.stage        = "welcome"
        self.mobile_no    = ""
        self.otp_sent     = ""
        self.otp_input    = ""
        self.account      = None
        self.withdraw_amt = 0
        self.pin_buffer   = ""
        self.is_duress    = False

        self.emotion_engine   = EmotionEngine(self.session_id)
        self.keystroke_engine = KeystrokeEngine()
        self.risk_engine      = RiskEngine(self.session_id)

        init_db()
        create_session(self.session_id)
        set_live("session_id", self.session_id)
        set_live("atm_stage",  "welcome")

        self._build_window()
        self.root.bind("<Key>", self._on_keyboard)
        self.emotion_engine.start()
        print(f"[ATM] Session {self.session_id} started")
        self._screen_welcome()

    def _build_window(self):
        self.root.title("SecureBank ATM — VaultEye")
        self.root.geometry("420x860")
        self.root.resizable(False, False)
        self.root.configure(bg=ATM_BG)

        hdr = tk.Frame(self.root, bg=ATM_PANEL, height=65)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  🏦  SecureBank ATM", bg=ATM_PANEL, fg=ATM_TEXT,
                 font=("Helvetica", 15, "bold")).pack(side=tk.LEFT, pady=17)
        tk.Label(hdr, text="●", bg=ATM_PANEL, fg=ATM_GREEN,
                 font=("Helvetica", 13)).pack(side=tk.RIGHT, padx=14)

        self.screen = tk.Frame(self.root, bg=ATM_BG, padx=22, pady=12)
        self.screen.pack(fill=tk.BOTH, expand=True)

        pad = tk.Frame(self.root, bg=ATM_PANEL, pady=8)
        pad.pack(fill=tk.X, side=tk.BOTTOM)
        self._build_keypad(pad)

    def _build_keypad(self, parent):
        for row_keys in [("1","2","3"),("4","5","6"),("7","8","9"),("CLR","0","ENT")]:
            rf = tk.Frame(parent, bg=ATM_PANEL)
            rf.pack(pady=3)
            for k in row_keys:
                bg = ATM_RED if k=="CLR" else (ATM_GREEN if k=="ENT" else ATM_BTN)
                tk.Button(rf, text=k, width=5, height=2, bg=bg, fg=ATM_TEXT,
                          font=("Helvetica", 15, "bold"), relief=tk.FLAT,
                          cursor="hand2", command=lambda key=k: self._on_key(key)
                          ).pack(side=tk.LEFT, padx=5)

    def _clear(self):
        for w in self.screen.winfo_children():
            w.destroy()

    def _sep(self):
        tk.Frame(self.screen, bg=ATM_BTN, height=2).pack(fill=tk.X, pady=7)

    def _title(self, text, fg=None):
        tk.Label(self.screen, text=text, bg=ATM_BG, fg=fg or ATM_TEXT,
                 font=("Helvetica", 16, "bold")).pack(pady=(12, 4))

    def _label(self, text, fg=None, size=12, pady=4):
        tk.Label(self.screen, text=text, bg=ATM_BG, fg=fg or ATM_TEXT,
                 font=("Helvetica", size)).pack(pady=pady)

    def _input_box(self, textvariable, width=14, size=22):
        lbl = tk.Label(self.screen, textvariable=textvariable,
                       bg=ATM_PANEL, fg=ATM_GREEN,
                       font=("Courier", size, "bold"), width=width, anchor="center")
        lbl.pack(pady=10, ipady=8)
        return lbl

    def _msg_label(self):
        lbl = tk.Label(self.screen, text="", bg=ATM_BG, fg=ATM_RED,
                       font=("Helvetica", 11))
        lbl.pack(pady=2)
        return lbl

    def _back_btn(self, cmd, text="← Back"):
        tk.Button(self.screen, text=text, bg=ATM_BTN, fg=ATM_TEXT,
                  font=("Helvetica", 10), relief=tk.FLAT,
                  cursor="hand2", command=cmd).pack(pady=6)

    def _big_btn(self, text, cmd, bg=None, width=24, height=2):
        tk.Button(self.screen, text=text, bg=bg or ATM_BTN, fg=ATM_TEXT,
                  font=("Helvetica", 13, "bold"), relief=tk.FLAT,
                  cursor="hand2", width=width, height=height,
                  command=cmd).pack(pady=8)

    # ── SCREEN 1: Welcome ────────────────────────────────────────────────────
    def _screen_welcome(self):
        self._clear()
        self.stage = "welcome"
        self.account = None
        self.mobile_no = ""
        self.withdraw_amt = 0
        self.pin_buffer = ""
        set_live("atm_stage", "welcome")

        tk.Label(self.screen, text="🏦  Welcome to SecureBank",
                 bg=ATM_BG, fg=ATM_TEXT,
                 font=("Helvetica", 18, "bold")).pack(pady=(22, 4))
        tk.Label(self.screen, text="Your trusted banking partner",
                 bg=ATM_BG, fg=ATM_YELLOW,
                 font=("Helvetica", 11, "italic")).pack()
        self._sep()
        self._label("Please select transaction type", fg=ATM_YELLOW, size=12, pady=10)
        self._big_btn("💳   CARD TRANSACTION", self._card_coming_soon, bg=ATM_BTN)
        tk.Label(self.screen, text="── or ──", bg=ATM_BG, fg="#555555",
                 font=("Helvetica", 10)).pack()
        self._big_btn("📱   CARDLESS TRANSACTION", self._screen_mobile_entry, bg="#0d3d6b")
        self._sep()
        self._label("🔒  Secured by VaultEye AI", fg="#444444", size=9)

    def _card_coming_soon(self):
        tip = tk.Label(self.screen,
                       text="⚠️  Card transaction not available at this kiosk.",
                       bg=ATM_BG, fg=ATM_RED, font=("Helvetica", 10))
        tip.pack()
        self.root.after(2500, tip.destroy)

    # ── SCREEN 2: Mobile Entry ───────────────────────────────────────────────
    def _screen_mobile_entry(self):
        self._clear()
        self.stage = "mobile_entry"
        self.mobile_no = ""
        set_live("atm_stage", "mobile_entry")
        self._title("📱  Cardless Transaction")
        self._sep()
        self._label("Enter Your Registered Mobile Number", fg=ATM_YELLOW, size=12)
        self.mob_var = tk.StringVar(value="")
        self._input_box(self.mob_var, width=13, size=22)
        self.mob_err = self._msg_label()
        self._sep()
        self._back_btn(self._screen_welcome)

    def _handle_mobile_key(self, key):
        if key == "CLR":
            self.mobile_no = self.mobile_no[:-1]
        elif key == "ENT":
            if len(self.mobile_no) == 10:
                self._validate_mobile()
            else:
                self.mob_err.config(text="Enter a valid 10-digit mobile number")
            return
        elif key.isdigit() and len(self.mobile_no) < 10:
            self.mobile_no += key
        self.mob_var.set(self.mobile_no or "")
        self.mob_err.config(text="")

    def _validate_mobile(self):
        if self.mobile_no in MOBILE_ACCOUNTS:
            self.account = MOBILE_ACCOUNTS[self.mobile_no]
            self._screen_otp_sending()
        else:
            self.mob_err.config(text="❌  Mobile number not registered!")
            self.mobile_no = ""
            self.mob_var.set("")

    # ── SCREEN 3: OTP ────────────────────────────────────────────────────────
    def _screen_otp_sending(self):
        self._clear()
        self.stage    = "otp_sending"
        self.otp_input = ""
        set_live("atm_stage", "otp_sending")
        self._title("📱  Sending OTP…")
        masked = self.mobile_no[:2] + "****" + self.mobile_no[-4:]
        self._label(f"Sending to  {masked}", fg=ATM_YELLOW, size=12)
        status = tk.StringVar(value="⏳  Connecting to network…")
        tk.Label(self.screen, textvariable=status, bg=ATM_BG, fg=ATM_BLUE,
                 font=("Helvetica", 11)).pack(pady=12)
        def _dispatch():
            ok, msg = send_otp(self.mobile_no)
            print(f"[OTP] {msg}")
            self.root.after(0, lambda: self._screen_otp_entry(ok, msg))
        threading.Thread(target=_dispatch, daemon=True).start()

    def _screen_otp_entry(self, sent_ok, send_msg):
        self._clear()
        self.stage = "otp_entry"
        self.otp_input = ""
        set_live("atm_stage", "otp_entry")
        self._title("🔐  OTP Verification")
        self._sep()
        masked = self.mobile_no[:2] + "****" + self.mobile_no[-4:]
        if sent_ok:
            self._label(f"✅  OTP sent to  {masked}", fg=ATM_GREEN, size=12)
            self._label("Check your SMS inbox", fg="#888888", size=10)
        else:
            self._label("⚠️  OTP sending failed!", fg=ATM_RED, size=10)
        self._sep()
        self._label("Enter 6-Digit OTP", fg=ATM_YELLOW, size=12)
        self.otp_var = tk.StringVar(value="_ _ _ _ _ _")
        self._input_box(self.otp_var, width=14, size=22)
        self.otp_err = self._msg_label()
        self._sep()
        row = tk.Frame(self.screen, bg=ATM_BG)
        row.pack()
        tk.Button(row, text="← Back", bg=ATM_BTN, fg=ATM_TEXT,
                  font=("Helvetica", 10), relief=tk.FLAT, cursor="hand2",
                  command=self._screen_mobile_entry).pack(side=tk.LEFT, padx=8)
        tk.Button(row, text="🔁  Resend OTP", bg=ATM_BTN, fg=ATM_YELLOW,
                  font=("Helvetica", 10), relief=tk.FLAT, cursor="hand2",
                  command=self._screen_otp_sending).pack(side=tk.LEFT, padx=8)

    def _handle_otp_key(self, key):
        if key == "CLR":
            self.otp_input = self.otp_input[:-1]
        elif key == "ENT":
            if len(self.otp_input) == 6:
                self._validate_otp()
            else:
                self.otp_err.config(text="Please enter all 6 digits")
            return
        elif key.isdigit() and len(self.otp_input) < 6:
            self.otp_input += key
        disp = " ".join("*" if i < len(self.otp_input) else "_" for i in range(6))
        self.otp_var.set(disp)
        self.otp_err.config(text="")

    def _validate_otp(self):
        if verify_otp(self.mobile_no, self.otp_input):
            self._screen_menu()
        else:
            self.otp_err.config(text="❌  Incorrect OTP! Try again.")
            self.otp_input = ""
            self.otp_var.set("_ _ _ _ _ _")

    # ── SCREEN 4: Menu ───────────────────────────────────────────────────────
    def _screen_menu(self):
        self._clear()
        self.stage = "menu"
        set_live("atm_stage", "menu")
        acct = self.account
        tk.Label(self.screen, text=f"Hello,  {acct['name'].split()[0]}!",
                 bg=ATM_BG, fg=ATM_GREEN,
                 font=("Helvetica", 18, "bold")).pack(pady=(14, 3))
        tk.Label(self.screen, text=f"A/C:  {acct['account']}",
                 bg=ATM_BG, fg=ATM_YELLOW, font=("Helvetica", 11)).pack()
        self._sep()
        self._label("What would you like to do?", fg=ATM_TEXT, size=12, pady=6)
        self._big_btn("💰   Check Balance",  self._screen_balance, bg=ATM_BTN)
        self._big_btn("💵   Withdraw Cash",  self._screen_withdraw_entry, bg="#0d5c2e")
        self._sep()
        self._big_btn("❌   Exit", self._screen_thankyou, bg=ATM_RED, height=1)

    # ── SCREEN 5a: Balance ───────────────────────────────────────────────────
    def _screen_balance(self):
        self._clear()
        self.stage = "balance"
        set_live("atm_stage", "balance")
        acct = self.account
        self._title("💰  Account Balance")
        self._sep()
        for lbl, val in [("Account Holder", acct["name"]),
                         ("Account No.", acct["account"]),
                         ("Date / Time", datetime.now().strftime("%d %b %Y   %H:%M:%S"))]:
            row = tk.Frame(self.screen, bg=ATM_BG)
            row.pack(fill=tk.X, padx=10, pady=3)
            tk.Label(row, text=lbl+":", bg=ATM_BG, fg=ATM_YELLOW,
                     font=("Helvetica", 11), width=16, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=val, bg=ATM_BG, fg=ATM_TEXT,
                     font=("Helvetica", 11, "bold"), anchor=tk.W).pack(side=tk.LEFT)
        self._sep()
        self._label("Available Balance", fg=ATM_YELLOW, size=13)
        tk.Label(self.screen, text=f"Rs.  {acct['balance']:,}",
                 bg=ATM_PANEL, fg=ATM_GREEN,
                 font=("Helvetica", 24, "bold"), padx=20, pady=10).pack(pady=6)
        self._sep()
        self._big_btn("← Back to Menu", self._screen_menu, bg=ATM_BTN, height=1)

    # ── SCREEN 5b: Withdraw Amount ───────────────────────────────────────────
    def _screen_withdraw_entry(self):
        self._clear()
        self.stage = "withdraw_entry"
        self.amt_input = ""
        set_live("atm_stage", "withdraw_entry")
        self._title("💵  Withdraw Cash")
        self._sep()
        self._label("Select or enter amount (Rs.)", fg=ATM_YELLOW, size=12)
        for i in range(0, 6, 3):
            row = tk.Frame(self.screen, bg=ATM_BG)
            row.pack(pady=3)
            for amt in [500, 1000, 2000, 5000, 10000, 20000][i:i+3]:
                tk.Button(row, text=f"{amt:,}", bg=ATM_BTN, fg=ATM_TEXT,
                          font=("Helvetica", 11, "bold"), relief=tk.FLAT,
                          cursor="hand2", width=7, height=2,
                          command=lambda a=amt: self._proceed_to_pin(a)
                          ).pack(side=tk.LEFT, padx=4)
        self._sep()
        self._label("Or type a custom amount and press ENT", fg="#888888", size=10)
        self.amt_var = tk.StringVar(value="")
        self._input_box(self.amt_var, width=12, size=20)
        self.amt_err = self._msg_label()
        self._back_btn(self._screen_menu)

    def _handle_amt_key(self, key):
        if key == "CLR":
            self.amt_input = self.amt_input[:-1]
        elif key == "ENT":
            if self.amt_input:
                self._proceed_to_pin(int(self.amt_input))
            else:
                self.amt_err.config(text="Please enter an amount first")
            return
        elif key.isdigit() and len(self.amt_input) < 7:
            self.amt_input += key
        self.amt_var.set(self.amt_input)
        self.amt_err.config(text="")

    def _proceed_to_pin(self, amount):
        acct = self.account
        if amount <= 0:
            self.amt_err.config(text="Amount must be greater than zero")
            return
        if amount % 100 != 0:
            self.amt_err.config(text="Amount must be in multiples of Rs.100")
            return
        if amount > acct["balance"]:
            self.amt_err.config(text=f"Insufficient balance!  Available: Rs.{acct['balance']:,}")
            return
        self.withdraw_amt = amount
        self._screen_pin_entry()

    # ── SCREEN 6: PIN Entry ──────────────────────────────────────────────────
    def _screen_pin_entry(self):
        self._clear()
        self.stage      = "pin"
        self.pin_buffer = ""
        self.is_duress  = False
        self.emotion_engine.reset()
        self.keystroke_engine.reset()
        set_live("atm_stage",     "pin")
        set_live("pin_submitted", "---")
        set_live("risk_score",     0)
        set_live("risk_level",    "LOW")
        set_live("is_duress",      False)

        acct = self.account
        tk.Label(self.screen, text=f"Withdrawal — Rs. {self.withdraw_amt:,}",
                 bg=ATM_BG, fg=ATM_GREEN,
                 font=("Helvetica", 14, "bold")).pack(pady=(14, 2))
        tk.Label(self.screen, text=f"A/C: {acct['account']}",
                 bg=ATM_BG, fg=ATM_YELLOW, font=("Helvetica", 11)).pack()
        self._sep()
        self.pin_msg = tk.Label(self.screen, text="Enter Your 4-Digit PIN",
                                bg=ATM_BG, fg=ATM_TEXT, font=("Helvetica", 13))
        self.pin_msg.pack(pady=6)
        self.pin_var = tk.StringVar(value="_ _ _ _")
        tk.Label(self.screen, textvariable=self.pin_var,
                 bg=ATM_PANEL, fg=ATM_GREEN,
                 font=("Courier", 26, "bold"), width=10).pack(pady=10)
        tk.Label(self.screen, text="🔒  AI Fraud Detection Active",
                 bg=ATM_BG, fg="#2a2a4a", font=("Helvetica", 9)).pack(pady=2)
        self._sep()
        tk.Button(self.screen, text="← Cancel", bg=ATM_RED, fg=ATM_TEXT,
                  font=("Helvetica", 10), relief=tk.FLAT, cursor="hand2",
                  command=self._screen_menu).pack(pady=4)

    def _handle_pin_key(self, key):
        if key == "CLR":
            self.pin_buffer = ""
            self.keystroke_engine.reset()
            self.pin_var.set("_ _ _ _")
            self.pin_msg.config(text="Enter Your 4-Digit PIN", fg=ATM_TEXT)
            return
        if key == "ENT":
            if len(self.pin_buffer) == PIN_LENGTH:
                self._submit_pin()
            return
        if key.isdigit() and len(self.pin_buffer) < PIN_LENGTH:
            self.pin_buffer += key
            self.keystroke_engine.record_keypress()
            disp = " ".join("*" if i < len(self.pin_buffer) else "_" for i in range(PIN_LENGTH))
            self.pin_var.set(disp)

    # ── UPDATED: _submit_pin with duress fix ─────────────────────────────────
    def _submit_pin(self):
        ks      = self.keystroke_engine.get_result()
        avg_emo = self.emotion_engine.get_averaged_score()
        result  = self.risk_engine.evaluate(
            self.pin_buffer, avg_emo, ks["risk_score"], ks["pattern"])
        set_live("pin_submitted",  result["pin_label"])
        set_live("last_ks_result", ks)
        self.is_duress = result.get("is_duress", False)

        if result["pin_label"] == "WRONG_PIN":
            self._wrong_pin()
        elif self.is_duress:
            # Show normal processing — thief won't suspect!
            self._screen_processing(duress=False)
            self.root.after(3000, self._screen_duress_success)
        else:
            self._screen_processing(duress=False)
            self.root.after(3000, self._screen_success)

    def _wrong_pin(self):
        self.pin_buffer = ""
        self.keystroke_engine.reset()
        self.pin_var.set("_ _ _ _")
        self.pin_msg.config(text="❌  Incorrect PIN! Try again", fg=ATM_RED)
        self.root.after(2000, lambda: self.pin_msg.config(
            text="Enter Your 4-Digit PIN", fg=ATM_TEXT))

    # ── SCREEN 7: Processing ─────────────────────────────────────────────────
    def _screen_processing(self, duress=False):
        self._clear()
        self.stage = "processing"
        set_live("atm_stage", "processing")
        tk.Label(self.screen, text="Processing…", bg=ATM_BG, fg=ATM_TEXT,
                 font=("Helvetica", 22, "bold")).pack(pady=40)
        tk.Label(self.screen, text="Please do not press any key",
                 bg=ATM_BG, fg=ATM_YELLOW, font=("Helvetica", 13)).pack()
        self._prog = tk.Canvas(self.screen, width=280, height=22,
                               bg=ATM_PANEL, highlightthickness=0)
        self._prog.pack(pady=22)
        self._anim_once(0)

    def _anim_once(self, step):
        if step <= 100:
            self._prog.delete("bar")
            self._prog.create_rectangle(0, 0, step*2.8, 22, fill=ATM_GREEN, tags="bar")
            self.root.after(28, lambda: self._anim_once(step+2))

    # ── SCREEN 8: Success ────────────────────────────────────────────────────
    def _screen_success(self):
        self._clear()
        acct = self.account
        acct["balance"] -= self.withdraw_amt
        set_live("atm_stage", "result")
        tk.Label(self.screen, text="✅  Transaction Successful",
                 bg=ATM_BG, fg=ATM_GREEN,
                 font=("Helvetica", 16, "bold")).pack(pady=(18, 6))
        self._sep()
        for lbl, val in [
            ("Amount Withdrawn",  f"Rs. {self.withdraw_amt:,}"),
            ("Available Balance", f"Rs. {acct['balance']:,}"),
            ("Account No.",       acct["account"]),
            ("Date / Time",       datetime.now().strftime("%d %b %Y   %H:%M:%S")),
            ("Txn ID",            f"TXN{self.session_id}"),
            ("Mode",              "Cardless"),
        ]:
            row = tk.Frame(self.screen, bg=ATM_BG)
            row.pack(fill=tk.X, padx=12, pady=3)
            tk.Label(row, text=lbl+":", bg=ATM_BG, fg=ATM_YELLOW,
                     font=("Helvetica", 11), width=18, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=val, bg=ATM_BG, fg=ATM_TEXT,
                     font=("Helvetica", 11, "bold"), anchor=tk.W).pack(side=tk.LEFT)
        self._sep()
        tk.Label(self.screen, text="Please collect your cash.\nThank you! 😊",
                 bg=ATM_BG, fg=ATM_TEXT,
                 font=("Helvetica", 12), justify=tk.CENTER).pack(pady=8)
        self.root.after(6000, self._screen_menu)

    # ── SCREEN 8b: Duress Success (fake) ─────────────────────────────────────
    def _screen_duress_success(self):
        self._clear()
        acct = self.account
        set_live("atm_stage", "duress_result")
        tk.Label(self.screen, text="✅  Transaction Successful",
                 bg=ATM_BG, fg=ATM_GREEN,
                 font=("Helvetica", 16, "bold")).pack(pady=(18, 6))
        self._sep()
        for lbl, val in [
            ("Amount Requested",  f"Rs. {self.withdraw_amt:,}"),
            ("Account No.",       acct["account"]),
            ("Date / Time",       datetime.now().strftime("%d %b %Y   %H:%M:%S")),
            ("Txn ID",            f"TXN{self.session_id}"),
            ("Mode",              "Cardless"),
        ]:
            row = tk.Frame(self.screen, bg=ATM_BG)
            row.pack(fill=tk.X, padx=12, pady=3)
            tk.Label(row, text=lbl+":", bg=ATM_BG, fg=ATM_YELLOW,
                     font=("Helvetica", 11), width=18, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=val, bg=ATM_BG, fg=ATM_TEXT,
                     font=("Helvetica", 11, "bold"), anchor=tk.W).pack(side=tk.LEFT)
        self._sep()
        # Fake dispenser error
        tk.Label(self.screen,
                 text="⚠️  Cash dispenser temporarily\nunavailable.\n\nPlease collect your card\nand visit the counter.",
                 bg=ATM_PANEL, fg=ATM_YELLOW,
                 font=("Helvetica", 12), justify=tk.CENTER,
                 padx=10, pady=10).pack(pady=10)
        self.root.after(7000, self._screen_welcome)

    # ── SCREEN 9: Thank You ──────────────────────────────────────────────────
    def _screen_thankyou(self):
        self._clear()
        self.stage = "exit"
        set_live("atm_stage", "exit")
        tk.Label(self.screen, text="Thank You!", bg=ATM_BG, fg=ATM_GREEN,
                 font=("Helvetica", 26, "bold")).pack(pady=44)
        tk.Label(self.screen, text="Have a great day 😊", bg=ATM_BG, fg=ATM_TEXT,
                 font=("Helvetica", 14)).pack()
        self._sep()
        tk.Label(self.screen, text="🔒  Protected by VaultEye AI Security",
                 bg=ATM_BG, fg="#444444", font=("Helvetica", 9)).pack(pady=8)
        self.root.after(5000, self._screen_welcome)

    # ── Key dispatcher ───────────────────────────────────────────────────────
    def _on_key(self, key):
        handlers = {
            "mobile_entry":   self._handle_mobile_key,
            "otp_entry":      self._handle_otp_key,
            "withdraw_entry": self._handle_amt_key,
            "pin":            self._handle_pin_key,
        }
        h = handlers.get(self.stage)
        if h:
            h(key)

    def _on_keyboard(self, event):
        if event.char.isdigit():
            self._on_key(event.char)
        elif event.keysym == "Return":
            self._on_key("ENT")
        elif event.keysym in ("BackSpace", "Delete"):
            self._on_key("CLR")