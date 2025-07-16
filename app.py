import os
import re
import uuid
import tempfile
import time
import shutil
import logging
from flask import Flask, request, render_template, Response
import yt_dlp

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instagram cookies for authentication
INSTAGRAM_COOKIES = {
    'sessionid': '62586856555%3AfsgYZEbHQoeBzh%3A7%3AAYcYcfwFDOeAG8It2VI5zdzLli3sWgHmlYSH617TzQ',
    'ds_user_id': '62586856555',
    'csrftoken': '8mn0V4PITQS8Bbre9YnCXc6nJvu5bB7n',
    'rur': '"CCO\05462586856555\0541782672276:01fe3977dba4fb4a7a6b3f8ebd51d43656d889c7027af1df04a33f1be93970966ff84c32"'
}

def create_instagram_cookies_file():
    """Create temporary cookies file in Netscape format"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tf:
        tf.write("# Netscape HTTP Cookie File\n")
        for name, value in INSTAGRAM_COOKIES.items():
            tf.write(f".instagram.com\tTRUE\t/\tTRUE\t2147483647\t{name}\t{value}\n")
        return tf.name

def clean_filename(title, resolution=None, ext='mp4'):
    """Clean filename with resolution and extension"""
    if not title:
        base = f"sapzap_{uuid.uuid4().hex[:8]}"
    else:
        clean = re.sub(r'[^\w\s-]', '', title).strip()
        clean = re.sub(r'[-\s]+', '_', clean)
        base = f"sapzap_{clean[:50]}"
    
    return f"{base}_{resolution}p.{ext}" if resolution else f"{base}.{ext}"

def download_media(url):
    """Download media with optimal settings using temporary directories"""
    is_youtube = 'youtube.com' in url or 'youtu.be' in url
    is_shorts = 'youtube.com/shorts' in url
    is_reels = 'instagram.com/reel' in url
    
    # Create a temporary directory for this download
    temp_dir = tempfile.mkdtemp()
    
    # Format selection logic
    ydl_opts = {
        'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'noplaylist': True,
        'merge_output_format': 'mp4',
        'retries': 3,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'windowsfilenames': True,
        'logger': logger
    }
    
    # YouTube format selection (simplified)
    if is_youtube and not is_shorts:
        # Reliable 1080p format selection
        ydl_opts['format'] = '(bestvideo[height<=1080][vcodec^=avc1]/bestvideo[height<=1080])+bestaudio'
    else:
        # Shorts/Reels - highest quality
        ydl_opts['format'] = 'best'
    
    cookies_file = None
    file_path = None
    
    try:
        # Handle Instagram with authentication
        if is_reels:
            cookies_file = create_instagram_cookies_file()
            ydl_opts['cookiefile'] = cookies_file
        
        # Execute download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp4')]
            
            if not downloaded_files:
                raise Exception("No files downloaded")
            
            file_path = os.path.join(temp_dir, downloaded_files[0])
            
            # Get resolution
            resolution = info.get('height') or (
                info.get('requested_formats')[0]['height'] 
                if info.get('requested_formats') 
                else None
            )
            
            # Create final filename
            title = info.get('title', 'video')
            filename = clean_filename(title, resolution)
            
            return file_path, filename, temp_dir
    
    except Exception as e:
        # Clean up if error occurs
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise e

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    if not url:
        return "URL is required", 400
    
    try:
        file_path, filename, temp_dir = download_media(url)
        
        # Create a streaming response
        def generate():
            with open(file_path, 'rb') as f:
                while chunk := f.read(1024 * 1024):  # 1MB chunks
                    yield chunk
            # Cleanup after streaming completes
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        response = Response(
            generate(),
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'video/mp4'
            }
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=False)
    