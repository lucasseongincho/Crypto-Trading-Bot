import os
import requests
from dotenv import load_dotenv

# Load environment variables once at the start of the module
load_dotenv()

# --- Load Telegram Credentials ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN").strip()
TELEGRAM_CHAT_ID = str(os.getenv("TELEGRAM_CHAT_ID")).strip()

def send_telegram_notification(message):
    """
    Sends a message to the specified Telegram chat using the bot.
    """
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("Telegram keys missing or not loaded. Notification not sent.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }

    try:
        response = requests.post(url, data=payload, timeout=5)
        response.raise_for_status()
        print(f"Notification sent: {message}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram notification: {response.status_code} {response.reason} for url: {url} | Details: {e}")