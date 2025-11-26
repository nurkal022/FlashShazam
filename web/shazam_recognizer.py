import asyncio
from shazamio import Shazam
from config import Config

class ShazamRecognizer:
    def __init__(self):
        self.shazam = Shazam()
    
    async def recognize(self, audio_file):
        """Распознает трек через Shazam"""
        try:
            result = await self.shazam.recognize(audio_file)
            
            if result and 'track' in result:
                track = result['track']
                return {
                    'title': track.get('title', 'Unknown'),
                    'artist': track.get('subtitle', 'Unknown'),
                    'shazam_id': track.get('key', ''),
                    'success': True
                }
            return {'success': False, 'error': 'Трек не найден'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def recognize_sync(self, audio_file):
        """Синхронная обертка для recognize"""
        return asyncio.run(self.recognize(audio_file))

