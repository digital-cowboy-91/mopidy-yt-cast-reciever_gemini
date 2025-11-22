import logging
import uuid
import time
import requests
import urllib.parse

logger = logging.getLogger(__name__)

LOUNGE_API_URL = 'https://www.youtube.com/api/lounge/pairing/'

class LoungeApi:
    def __init__(self, config):
        self.screen_name = config.get('yt_cast', {}).get('friendly_name', 'Mopidy Cast')
        self.screen_id = self._get_or_create_screen_id()
        self.lounge_token = None
        
    def _get_or_create_screen_id(self):
        # TODO: Persist this to disk so it survives restarts
        # For now, we'll generate a new one each time, which means re-pairing on restart
        return str(uuid.uuid4())

    def bind(self):
        """
        Registers the screen with YouTube to get a lounge_token.
        This is a simplified version of the bind process.
        """
        logger.info(f"Binding screen '{self.screen_name}' (ID: {self.screen_id}) to YouTube Lounge...")
        
        # The bind process is complex and involves multiple requests in the official client.
        # However, for just getting a pairing code, we might be able to use a simplified registration.
        # Based on reverse engineering, we need to hit the 'register_screen' endpoint first?
        # Or directly 'get_lounge_token_batch'?
        
        # Let's try to mimic the node.js implementation's registration flow.
        # It seems to use `https://www.youtube.com/api/lounge/bc/bind` for the actual session,
        # but for pairing code, we need a screen registered.
        
        # Actually, the node.js code uses `https://www.youtube.com/api/lounge/pairing/register_screen`
        # to get the lounge_token.
        
        url = 'https://www.youtube.com/api/lounge/pairing/register_screen'
        data = {
            'screen_id': self.screen_id,
            'screen_name': self.screen_name,
            'screen_app': 'yt-cast-receiver', # Or 'youtube-tv'
            'lounge_token': '', # Empty for new registration
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            result = response.json()
            
            if 'lounge_token' in result:
                self.lounge_token = result['lounge_token']
                logger.info(f"Successfully bound to Lounge. Token: {self.lounge_token}")
                return True
            else:
                logger.error(f"Failed to get lounge_token. Response: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error binding to Lounge: {e}")
            return False

    def get_pairing_code(self):
        if not self.lounge_token:
            if not self.bind():
                return None

        url = 'https://www.youtube.com/api/lounge/pairing/get_pairing_code'
        data = {
            'access_type': 'permanent',
            'app': 'yt-cast-receiver',
            'lounge_token': self.lounge_token,
            'screen_id': self.screen_id,
            'screen_name': self.screen_name
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            # Response is usually just the code as string or simple text
            code = response.text.replace('-', ' ').strip()
            
            # Format it nicely XXX XXX XXX
            if len(code) == 9: # 123456789
                 formatted_code = f"{code[:3]} {code[3:6]} {code[6:]}"
                 return formatted_code
            elif len(code) == 11: # 123 456 789 (already formatted?)
                 return code
            
            return code
            
        except Exception as e:
            logger.error(f"Error getting pairing code: {e}")
            return None
