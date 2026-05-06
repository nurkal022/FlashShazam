import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SHAZAM_API_KEY = os.getenv('SHAZAM_API_KEY', '')
    APIFY_TOKEN = os.getenv('APIFY_TOKEN', '')

    RECORDING_DURATION = 15  # секунд
    RECORDINGS_DIR = 'recordings'
    DOWNLOADS_DIR = 'downloads'

    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
