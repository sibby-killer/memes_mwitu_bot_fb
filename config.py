import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Facebook Secrets
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

# Verify configuration (Optional, useful to catch missing keys early)
def verify_config():
    missing = []
    if not TELEGRAM_BOT_TOKEN: missing.append("TELEGRAM_BOT_TOKEN")
    if not GROQ_API_KEY: missing.append("GROQ_API_KEY")
    if not FACEBOOK_PAGE_ID: missing.append("FACEBOOK_PAGE_ID")
    if not FACEBOOK_PAGE_ACCESS_TOKEN: missing.append("FACEBOOK_PAGE_ACCESS_TOKEN")

    if missing:
        raise ValueError(f"Missing essential configuration variables in .env: {', '.join(missing)}")

if __name__ == "__main__":
    verify_config()
    print("Configuration loaded successfully!")
