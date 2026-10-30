
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]
API_BASE_URL = os.environ["API_BASE_URL"].rstrip("/")

PROXY = os.getenv("PROXY") or None

API_TOKEN = os.getenv("API_TOKEN")
