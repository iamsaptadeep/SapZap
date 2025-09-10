import os

# YouTube PO Token (if available)
YT_PO_TOKEN = os.environ.get('YT_PO_TOKEN', '')

# YouTube cookies (if available)
YOUTUBE_COOKIES = {
    'SID': os.environ.get('YOUTUBE_SID', ''),
    'HSID': os.environ.get('YOUTUBE_HSID', ''),
    'SSID': os.environ.get('YOUTUBE_SSID', ''),
    'APISID': os.environ.get('YOUTUBE_APISID', ''),
    'SAPISID': os.environ.get('YOUTUBE_SAPISID', ''),
    'LOGIN_INFO': os.environ.get('YOUTUBE_LOGIN_INFO', ''),
}

# Instagram cookies (if available)
INSTAGRAM_COOKIES = {
    'sessionid': os.environ.get('INSTAGRAM_SESSIONID', ''),
    'ds_user_id': os.environ.get('INSTAGRAM_DS_USER_ID', ''),
    'csrftoken': os.environ.get('INSTAGRAM_CSRFTOKEN', ''),
}

# Application settings
class Config:
    DEBUG = False
    MAX_CONTENT_LENGTH = 5000 * 1024 * 1024  # 500MB max file size
    TEMP_DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'temp_downloads')
    ALLOWED_EXTENSIONS = {'mp4', 'webm', 'mkv'}
    
    # Rate limiting
    DOWNLOAD_DELAY = 2  # seconds between downloads
    
    @staticmethod
    def init_app(app):
        if not os.path.exists(Config.TEMP_DOWNLOAD_FOLDER):
            os.makedirs(Config.TEMP_DOWNLOAD_FOLDER)


