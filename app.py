import os
import re
import uuid
import random
import tempfile
import shutil
import logging
import time
import subprocess
import sys
from flask import Flask, request, render_template, Response
import yt_dlp
from yt_dlp.utils import DownloadError

# Try to install PO Token plugin for better YouTube support
def install_po_token_plugin():
    """Install PO Token plugin if not already installed."""
    try:
        import yt_dlp_get_pot
        logger.info("✅ PO Token plugin already installed")
        return True
    except ImportError:
        try:
            logger.info("📦 Installing PO Token plugin for better YouTube support...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp-get-pot", "--quiet"])
            logger.info("✅ PO Token plugin installed successfully")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Could not install PO Token plugin: {e}")
            return False

def create_base_ydl_opts(temp_dir, headers, cookies_file=None):
    """Create base yt-dlp options without PO Token plugin."""
    opts = {
        'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'noplaylist': True,
        'retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,
        'windowsfilenames': True,
        'logger': logger,
        'noprogress': True,
        'http_headers': headers,
        'nocheckcertificate': True,
        'sleep_interval': random.uniform(1, 3),
        'max_sleep_interval': 5,
        'geo_bypass': True,
        'geo_bypass_country': 'US',
    }
    
    if cookies_file:
        opts['cookiefile'] = cookies_file
        
    return opts

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to install PO token plugin on startup
install_po_token_plugin()

# Updated Instagram cookies - refresh these periodically
INSTAGRAM_COOKIES = {
    'sessionid': '62586856555%3AUrJiGyKV2H6db0%3A7%3AAYdxkb-PFtr2tdKmoM7ecXV3Wltfj08R1ljvQ61GYA',
    'ds_user_id': '62586856555',
    'csrftoken': 'N7J4wem0oKB16aRfi5zX8u',
    'rur': '"HIL\05462586856555\0541785099262:01fe44bdea098b826d993cce284d6b774aaf32384da9b09458a4e1f4c60b78e008390929"'
}

# YouTube cookies template - users should replace with their own
YOUTUBE_COOKIES = {
    'VISITOR_INFO1_LIVE': 'b7a_E1WVJPs',
    'YSC': 'H-_G9xY79AE',
    'SID': 'g.a000zgjGCJyQc0bL3wr4HGWnrL21w6Ati0aw0DYAOoHZ7QeSGe0vFj0ULa7Q47NHAJMVtEuqrAACgYKAZoSARcSFQHGX2Mi8QVOYvhY5vlwv1rhakD57BoVAUF8yKrpj64NGFnVEe2cQDAjtqJE0076',
    'SAPISID': 'XYUczUcvjVY7yZj0/AQGWubmQnegiTQSIN',
}




# Regex to find video IDs from all common YouTube URL formats
YOUTUBE_REGEX = re.compile(r'(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([\w-]+)')

# Enhanced user agents with more variety
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/131.0.0.0 Safari/537.36'
]

def create_cookies_file(cookies_dict):
    """Creates a temporary cookie file for yt-dlp to use."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tf:
        tf.write("# Netscape HTTP Cookie File\n")
        domain = ".youtube.com" if 'VISITOR_INFO1_LIVE' in str(cookies_dict) else ".instagram.com"
        for name, value in cookies_dict.items():
            tf.write(f"{domain}\tTRUE\t/\tTRUE\t2147483647\t{name}\t{value}\n")
        return tf.name

def clean_filename(title, resolution=None, ext='mp4'):
    """Generates a clean, safe filename for the downloaded media."""
    if not title:
        base = f"sapzap_{uuid.uuid4().hex[:8]}"
    else:
        clean = re.sub(r'[^\w\s-]', '', title).strip()
        clean = re.sub(r'[-\s]+', '_', clean)
        base = f"sapzap_{clean[:50]}"
    return f"{base}_{resolution}p.{ext}" if resolution else f"{base}.{ext}"

def normalize_youtube_url(raw_url):
    """Normalize YouTube URL for consistent processing."""
    youtube_match = YOUTUBE_REGEX.search(raw_url)
    if youtube_match:
        video_id = youtube_match.group(1)
        normalized_url = f'https://www.youtube.com/watch?v={video_id}'
        logger.info(f"Normalized YouTube URL for ID: {video_id}")
        return normalized_url, video_id, 'shorts' in raw_url
    return None, None, False

def download_media(original_url):
    """
    Downloads media with enhanced bot detection avoidance and consistent quality.
    """
    raw_url = original_url.strip()
    temp_dir = tempfile.mkdtemp()
    cookies_file = None

    try:
        # Random user agent selection
        user_agent = random.choice(USER_AGENTS)
        
        # Enhanced headers to appear more like a regular browser
        headers = {
            'User-Agent': user_agent,
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # Base yt-dlp options with anti-bot measures
        ydl_opts = {
            'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            # Reduced retries to avoid triggering rate limiting
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'windowsfilenames': True,
            'logger': logger,
            'noprogress': True,
            'http_headers': headers,
            'nocheckcertificate': True,
            # Add random delays between requests
            'sleep_interval': random.uniform(1, 3),
            'max_sleep_interval': 5,
            # Geo bypass attempts
            'geo_bypass': True,
            'geo_bypass_country': 'US',
        }

        # Check if it's a YouTube URL
        normalized_url, video_id, is_shorts = normalize_youtube_url(raw_url)
        
        if normalized_url:
            logger.info("YouTube video URL detected.")
            url = normalized_url
            
            # First try with PO Token plugin enabled
            try:
                # Enhanced YouTube-specific configuration with PO Token workarounds
                ydl_opts.update({
                    'http_headers': {
                        **headers,
                        'Referer': 'https://www.youtube.com/',
                        'Origin': 'https://www.youtube.com',
                        'X-YouTube-Client-Name': '1',
                        'X-YouTube-Client-Version': '2.20250101.01.00',
                    },
                    'extractor_args': {
                        'youtube': {
                            # Try multiple clients, prioritizing those that work without PO tokens
                            'player_client': ['mediaconnect', 'web', 'ios', 'android'],
                            'player_skip': ['webpage'],
                            'lang': ['en'],
                            # Enable missing PO token formats as fallback
                            'formats': ['missing_pot'],
                            # Skip clients that require PO tokens if not available
                            'skip_dash_manifest': False,
                        }
                    }
                })
                
                # Advanced format selection with PO Token bypass strategies
                if is_shorts:
                    logger.info("YouTube Shorts detected - using PO Token bypass strategy")
                    # Try multiple format combinations for Shorts
                    ydl_opts['format'] = (
                        # First try: Best quality without PO token requirements
                        'bestvideo[height<=2160][ext=mp4][protocol^=https]+bestaudio[ext=m4a][protocol^=https]/'
                        # Fallback to single format files
                        'best[ext=mp4][height<=2160][protocol^=https]/'
                        'best[ext=mp4][height<=1440][protocol^=https]/'
                        'best[ext=mp4][height<=1080][protocol^=https]/'
                        'best[ext=mp4][height<=720][protocol^=https]/'
                        # Final fallback to any available format
                        'best[ext=mp4]/best'
                    )
                else:
                    logger.info("YouTube video detected - using multi-client strategy")
                    # For regular videos, try various quality levels with fallbacks
                    ydl_opts['format'] = (
                        # Try to get 1080p without PO tokens
                        'bestvideo[height<=1080][ext=mp4][protocol^=https]+bestaudio[ext=m4a][protocol^=https]/'
                        # Single file fallbacks
                        'best[ext=mp4][height<=1080][protocol^=https]/'
                        'best[ext=mp4][height<=720][protocol^=https]/'
                        'bestvideo[height<=720][ext=mp4][protocol^=https]+bestaudio[ext=m4a][protocol^=https]/'
                        # Accept any mp4 format as final fallback
                        'best[ext=mp4]/best'
                    )
                
            except Exception as e:
                logger.warning(f"PO Token plugin configuration failed: {e}")
                # Fall back to basic configuration
                ydl_opts.update({
                    'http_headers': {
                        **headers,
                        'Referer': 'https://www.youtube.com/',
                    },
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['ios', 'web'],
                            'lang': ['en'],
                        }
                    }
                })
                
                # Simplified format selection
                if is_shorts:
                    ydl_opts['format'] = 'best[height<=2160]/best[height<=1440]/best'
                else:
                    ydl_opts['format'] = 'best[height<=1080]/best[height<=720]/best'
            
            # Use cookies if available to avoid bot detection
            if YOUTUBE_COOKIES:
                cookies_file = create_cookies_file(YOUTUBE_COOKIES)
                ydl_opts['cookiefile'] = cookies_file
                logger.info("Using YouTube cookies for authentication")
            else:
                logger.warning("No YouTube cookies configured - may encounter bot detection")

        elif 'instagram.com/reel' in raw_url:
            logger.info("Instagram Reel URL detected.")
            url = raw_url
            ydl_opts['format'] = 'best'
            cookies_file = create_cookies_file(INSTAGRAM_COOKIES)
            ydl_opts['cookiefile'] = cookies_file
            
        else:
            raise ValueError("Unsupported URL. Please provide a valid YouTube or Instagram Reel link.")

        # Perform the download with multiple attempts using different strategies
        max_attempts = 3
        last_error = None
        info = None  # Initialize info variable
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Download attempt {attempt + 1}/{max_attempts}")
                
                # Modify strategy based on attempt number
                if attempt == 1:
                    # Second attempt: Force web client only and disable PO Token plugin
                    if 'extractor_args' in ydl_opts:
                        ydl_opts['extractor_args']['youtube']['player_client'] = ['web']
                        # Remove PO Token plugin to avoid JSON errors
                        ydl_opts['extractor_args']['youtube'].pop('formats', None)
                        logger.info("Retry with web client only, PO Token plugin disabled")
                elif attempt == 2:
                    # Third attempt: Use standard yt-dlp without PO Token plugin
                    # Remove PO Token plugin completely for this attempt
                    try:
                        # Temporarily disable the plugin by creating fresh ydl_opts
                        fallback_opts = {
                            'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
                            'quiet': False,
                            'no_warnings': False,
                            'noplaylist': True,
                            'retries': 1,
                            'fragment_retries': 1,
                            'skip_unavailable_fragments': True,
                            'windowsfilenames': True,
                            'logger': logger,
                            'noprogress': True,
                            'http_headers': headers,
                            'nocheckcertificate': True,
                            'sleep_interval': 1,
                            'max_sleep_interval': 3,
                            'geo_bypass': True,
                            'geo_bypass_country': 'US',
                            'extractor_args': {
                                'youtube': {
                                    'player_client': ['ios'],
                                    'player_skip': ['webpage'],
                                    'lang': ['en'],
                                }
                            }
                        }
                        
                        # Use simplified format selection for iOS client
                        if is_shorts:
                            fallback_opts['format'] = 'best[height<=2160]/best[height<=1440]/best[height<=1080]/best'
                        else:
                            fallback_opts['format'] = 'best[height<=1080]/best[height<=720]/best'
                        
                        # Add cookies if available
                        if cookies_file:
                            fallback_opts['cookiefile'] = cookies_file
                            
                        logger.info("Retry with iOS client and standard yt-dlp (no PO Token plugin)")
                        ydl_opts = fallback_opts
                    except Exception as e:
                        logger.warning(f"Failed to create fallback options: {e}")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                
                # If we get here, download succeeded
                break
                
            except DownloadError as e:
                last_error = e
                error_msg = str(e).lower()
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if 'bot' in error_msg or 'sign in' in error_msg:
                    logger.error("YouTube bot detection triggered on all attempts")
                    if attempt == max_attempts - 1:  # Last attempt
                        raise RuntimeError(
                            "YouTube detected automated access after multiple attempts. "
                            "Please try again later or configure YouTube cookies for authentication."
                        )
                elif 'json' in error_msg or 'player response' in error_msg:
                    logger.warning("JSON parsing error - likely PO Token plugin issue")
                
                # Add delay between attempts
                if attempt < max_attempts - 1:
                    delay = random.uniform(2, 5)
                    logger.info(f"Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
            
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed with unexpected error: {e}")
                if attempt == max_attempts - 1:
                    raise
                
                # Short delay before retry
                time.sleep(1)
        
        # Check if we got valid info
        if not info:
            if last_error:
                raise last_error
            else:
                raise RuntimeError("All download attempts failed without extracting video info")

        # Find downloaded file
        files = [f for f in os.listdir(temp_dir) if f.lower().endswith(('.mp4', '.mkv', '.webm'))]
        if not files:
            raise RuntimeError("Download succeeded, but no media file was found.")
        
        file_path = os.path.join(temp_dir, files[0])
        
        # Generate filename with resolution info and log the actual quality
        final_height = info.get('height')
        final_width = info.get('width')
        format_id = info.get('format_id', 'unknown')
        
        logger.info(f"📹 Downloaded format: {format_id}, Resolution: {final_width}x{final_height}")
        
        # Check if we got lower quality than expected and warn
        if is_shorts and final_height and final_height < 720:
            logger.warning(f"⚠️ Shorts downloaded at {final_height}p - lower than expected due to PO Token restrictions")
        elif not is_shorts and final_height and final_height < 720:
            logger.warning(f"⚠️ Video downloaded at {final_height}p - consider adding PO Token support for higher quality")
        
        filename = clean_filename(info.get('title', 'video'), final_height)

        logger.info(f"Successfully downloaded: {filename}")
        return file_path, filename, temp_dir

    except DownloadError as de:
        logger.error(f"yt-dlp download failed for URL {original_url}: {de}")
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        error_msg = str(de).lower()
        if 'bot' in error_msg or 'sign in' in error_msg:
            raise RuntimeError(
                "YouTube is blocking downloads. This usually happens due to:\n"
                "1. Too many requests from your IP\n"
                "2. Missing authentication cookies\n"
                "Please try again later or contact the administrator."
            )
        elif 'unavailable' in error_msg:
            raise RuntimeError("This video is unavailable or has been removed.")
        else:
            raise RuntimeError("Download failed. Please check the URL and try again.")
            
    except Exception as e:
        logger.error(f"Unexpected error for URL {original_url}: {e}")
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"An unexpected error occurred: {str(e)}")
        
    finally:
        if cookies_file and os.path.exists(cookies_file):
            os.unlink(cookies_file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url', '')
    if not url:
        return "URL is required.", 400

    try:
        file_path, filename, temp_dir = download_media(url)

        def generate():
            try:
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(1024 * 1024)  # 1MB chunks
                        if not chunk:
                            break
                        yield chunk
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        # Determine MIME type
        ext = os.path.splitext(filename)[1][1:].lower()
        mime_types = {
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'mkv': 'video/x-matroska'
        }
        mime = mime_types.get(ext, 'application/octet-stream')

        return Response(
            generate(),
            mimetype=mime,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': mime
            }
        )

    except (ValueError, RuntimeError) as e:
        logger.warning(f"Download failed for '{url}': {e}")
        return str(e), 400
    except Exception as e:
        logger.error(f"Critical error during download from '{url}': {e}")
        return "A server error occurred. Please check the link or try again later.", 500

if __name__ == '__main__':
    # Print startup message with cookie configuration info
    print("\n" + "="*60)
    print("📺 SapZap YouTube/Instagram Downloader")
    print("="*60)
    if not YOUTUBE_COOKIES:
        print("⚠️  WARNING: No YouTube cookies configured!")
        print("   You may encounter 'bot detection' errors.")
        print("   To fix this, add your YouTube cookies to the")
        print("   YOUTUBE_COOKIES dictionary in the code.")
        print("   See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ")
    else:
        print("✅ YouTube cookies configured")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


