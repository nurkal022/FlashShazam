import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Shazam API (shazam-api.com)
    SHAZAM_API_KEY = os.getenv('SHAZAM_API_KEY', '')
    
    # Apify для скачивания с Spotify
    APIFY_TOKEN = os.getenv('APIFY_TOKEN', '')
    
    # Spotify Web API для поиска треков
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')

    RECORDING_DURATION = 15  # секунд
    RECORDINGS_DIR = 'recordings'
    DOWNLOADS_DIR = 'downloads'

    # Создаем директории если их нет
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

