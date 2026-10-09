from twilio.rest import Client
import otp_config as cfg
import random

ACCOUNT_SID = "your_twilio_account_sid"
AUTH_TOKEN = "your_twilio_auth_token"
SERVICE_SID = "your_twilio_service_sid"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def generate_otp(length=6):
    return str(random.randint(10**(length-1), 10**length - 1))

def send_otp(mobile: str, otp: str = None):
    provider = getattr(cfg, "OTP_PROVIDER", "twilio").lower()
    if provider == "twilio":
        return _send_twilio(mobile)
    else:
        return _send_console(mobile)

def _send_twilio(mobile: str):
    try:
        verification = client.verify.v2.services(SERVICE_SID) \
            .verifications \
            .create(to=f"+91{mobile}", channel="sms")
        return True, "OTP sent via Twilio"
    except Exception as e:
        return False, f"Twilio error: {e}"

def verify_otp(mobile: str, otp_code: str):
    try:
        result = client.verify.v2.services(SERVICE_SID) \
            .verification_checks \
            .create(to=f"+91{mobile}", code=otp_code)
        return result.status == "approved"
    except Exception as e:
        print(f"Twilio verify error: {e}")
        return False

def _send_console(mobile, otp=None):
    print(f"[OTP CONSOLE] Mobile: {mobile}")
    return False, "OTP printed to console"