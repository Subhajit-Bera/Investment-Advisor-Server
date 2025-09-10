import random
import string
from app.core.config import settings

def generate_otp(length: int = 6) -> str:
    """Generates a random OTP."""
    return ''.join(random.choices(string.digits, k=length))

async def send_otp_email(email: str, otp: str):
    """
    Sends the OTP to the user's email.
    This is a placeholder. In a real application, you would integrate this
    with a transactional email service like SendGrid, Mailgun, or AWS SES.
    """
    print("--- EMAIL SERVICE (MOCK) ---")
    print(f"Sending OTP to: {email}")
    print(f"OTP Code: {otp}")
    print(f"Using API Key: {settings.EMAIL_API_KEY[:5]}...")
    print("--- END EMAIL SERVICE ---")
    return True