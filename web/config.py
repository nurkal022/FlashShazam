import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SHAZAM_API_KEY = os.getenv('SHAZAM_API_KEY', '')
    RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '')
    RAPIDAPI_HOST = os.getenv('RAPIDAPI_HOST', 'spotify-downloader9.p.rapidapi.com')
    
    RECORDING_DURATION = 15  # секунд
    RECORDINGS_DIR = 'recordings'
    DOWNLOADS_DIR = 'downloads'
    
    # Создаем директории если их нет
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

