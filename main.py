import logging
logging.getLogger('twilio').setLevel(logging.WARNING)
import os
import warnings

# Suppress all TensorFlow and Keras warnings
os.environ['TF_ENABLE_ONEDNN_OPTS']  = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL']   = '3'
os.environ['PYTHONWARNINGS']         = 'ignore'
warnings.filterwarnings('ignore')

# Must be imported AFTER setting environment variables
import tkinter as tk
from atm_interface import ATMInterface
from backend_monitor import BackendMonitor
from database import init_db

if __name__ == "__main__":
    init_db()

    atm_root     = tk.Tk()
    atm_app      = ATMInterface(atm_root)

    monitor_root = tk.Toplevel(atm_root)
    monitor_app  = BackendMonitor(monitor_root)

    atm_root.mainloop()