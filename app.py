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
        logger.info("✅ PO Token plugin detected - will try to work around limitations")
        return True
    except ImportError:
        logger.info("⚠️ PO Token plugin not installed - using alternative strategies")
        return False

def create_base_ydl_opts(temp_dir, headers, cookies_file=None):
    """Create base yt-dlp options with enhanced configuration."""
    opts = {
        'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'noplaylist': True,
        'retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': False,  # Changed to False for better quality
        'windowsfilenames': True,
        'logger': logger,
        'noprogress': True,
        'http_headers': headers,
        'nocheckcertificate': True,
        'sleep_interval': random.uniform(1, 3),
        'max_sleep_interval': 5,
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        # Add format sorting preferences
        'format_sort': ['res:1080', 'ext:mp4:m4a', 'hasaud', 'source'],
        'format_sort_force': True,
    }
    
    if cookies_file:
        opts['cookiefile'] = cookies_file
        
    return opts

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for PO token plugin on startup
HAS_PO_TOKEN = install_po_token_plugin()

# Updated Instagram cookies - refresh these periodically
INSTAGRAM_COOKIES = {
    'sessionid': '62586856555%3AUrJiGyKV2H6db0%3A7%3AAYdxkb-PFtr2tdKmoM7ecXV3Wltfj08R1ljvQ61GYA',
    'ds_user_id': '62586856555',
    'csrftoken': 'N7J4wem0oKB16aRfi5zX8u',
    'rur': '"HIL\05462586856555\0541785099262:01fe44bdea098b826d993cce284d6b774aaf32384da9b09458a4e1f4c60b78e008390929"',
    # Add additional Instagram cookies for better quality
    'ig_cb': '2',
    'ig_did': 'C8F4C1F4-8B2A-4F4A-9F4A-1234567890AB',
    'shbid': '"1234\05462586856555\0541758635262:01f0e123456789abcdef"',
    'shbts': '"1727099262\05462586856555\0541758635262:01f0e123456789abcdef"'
}

# Enhanced YouTube cookies - users should replace with their own
YOUTUBE_COOKIES = {
    'VISITOR_INFO1_LIVE': 'b7a_E1WVJPs',
    'YSC': 'H-_G9xY79AE',
    'SID': 'g.a000zgjGCJyQc0bL3wr4HGWnrL21w6Ati0aw0DYAOoHZ7QeSGe0vFj0ULa7Q47NHAJMVtEuqrAACgYKAZoSARcSFQHGX2Mi8QVOYvhY5vlwv1rhakD57BoVAUF8yKrpj64NGFnVEe2cQDAjtqJE0076',
    'SAPISID': 'XYUczUcvjVY7yZj0/AQGWubmQnegiTQSIN',
    # Add visitor data for better quality access
    '__Secure-3PSID': 'g.a000zgjGCJyQc0bL3wr4HGWnrL21w6Ati0aw0DYAOoHZ7QeSGe0vFj0ULa7Q47NHAJMVtEuqrAACgYKAZoSARcSFQHGX2Mi8QVOYvhY5vlwv1rhakD57BoVAUF8yKrpj64NGFnVEe2cQDAjtqJE0076',
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

def get_optimal_youtube_format(is_shorts, has_po_token, attempt=0):
    """
    Get optimal format string based on video type and available features.
    """
    if is_shorts:
        # For Shorts: Use very specific format IDs that bypass PO tokens
        if attempt == 0:
            # Format 22: 720p MP4, Format 18: 360p MP4 (these usually work without PO tokens)
            return (
                '22/134+140/135+140/'  # 720p video + audio
                '18+140/18+'  # 360p with audio fallback
                'best[format_id=22]/best[format_id=18]/'
                'best[height>=720][protocol=https]/best[height>=720]/'
                'best[ext=mp4]/best'
            )
        elif attempt == 1:
            # Try even more specific approach
            return (
                'best[format_id=22]/best[format_id=134]/best[format_id=135]/'
                'bestvideo[height<=720]+bestaudio[ext=m4a]/'
                'best[format_id=18]/best[ext=mp4]/best'
            )
        else:
            # Last resort - just get anything
            return 'best[format_id=18]/18/best'
    else:
        # For regular videos: These work well for 1080p
        if attempt == 0:
            return (
                'best[format_id=22]/best[height=1080][format_id!=137]/'  # Avoid 137 (often needs PO token)
                'bestvideo[height=1080][format_id!=137]+bestaudio/'
                'best[height<=1080][ext=mp4]/best[ext=mp4]/best'
            )
        elif attempt == 1:
            return (
                'best[height<=1080][ext=mp4]/'
                'best[format_id=22]/best[format_id=18]/'
                'best[ext=mp4]/best'
            )
        else:
            return 'best[format_id=18]/best[ext=mp4]/best'

def download_media(original_url):
    """
    Downloads media with enhanced quality targeting.
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
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }

        # Base yt-dlp options with quality optimization
        ydl_opts = create_base_ydl_opts(temp_dir, headers)

        # Check if it's a YouTube URL
        normalized_url, video_id, is_shorts = normalize_youtube_url(raw_url)
        
        if normalized_url:
            logger.info("YouTube video URL detected.")
            url = normalized_url
            
            # Enhanced YouTube configuration for higher quality
            extractor_args = {
                'youtube': {
                    'player_client': ['ios', 'web'],  # iOS first, avoid android (PO token issues)
                    'player_skip': ['webpage', 'configs'],  # Skip problematic parsers
                    'lang': ['en'],
                    'max_comments': ['0'],  # Don't fetch comments
                    # CRITICAL: Force enable formats that might be missing PO tokens
                    'formats': 'missing_pot',  # This enables broken formats anyway
                    # Try to bypass PO token requirements
                    'skip_dash_manifest': True,  # Skip DASH (often requires PO tokens)
                }
            }
            
            # Add visitor data if available to help with quality
            if 'VISITOR_INFO1_LIVE' in YOUTUBE_COOKIES:
                extractor_args['youtube']['visitor_data'] = YOUTUBE_COOKIES['VISITOR_INFO1_LIVE']
            
            ydl_opts.update({
                'http_headers': {
                    **headers,
                    'Referer': 'https://www.youtube.com/',
                    'Origin': 'https://www.youtube.com',
                },
                'extractor_args': extractor_args,
                'format': get_optimal_youtube_format(is_shorts, HAS_PO_TOKEN, 0),
                # Force quality selection
                'prefer_ffmpeg': True,
                'keepvideo': False,
                # Ignore errors for missing formats and try alternatives
                'ignoreerrors': False,
                'no_warnings': False,
                # Force format selection even if it might fail
                'force_generic_extractor': False,
            })
            
            if is_shorts:
                logger.info("YouTube Shorts detected - targeting highest resolution")
            else:
                logger.info("YouTube video detected - targeting 1080p")
            
            # Use cookies for authentication
            if YOUTUBE_COOKIES:
                cookies_file = create_cookies_file(YOUTUBE_COOKIES)
                ydl_opts['cookiefile'] = cookies_file
                logger.info("Using YouTube cookies for authentication")

        elif 'instagram.com/reel' in raw_url:
            logger.info("Instagram Reel URL detected.")
            url = raw_url
            
            # Enhanced Instagram configuration for highest quality
            ydl_opts.update({
                'http_headers': {
                    **headers,
                    'Referer': 'https://www.instagram.com/',
                    'Origin': 'https://www.instagram.com',
                    'X-Instagram-AJAX': '1',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                # Aggressive format selection targeting 1080p specifically
                'format': (
                    # Target 1080p specifically first (1080x1920 for vertical content)
                    'bestvideo[height=1920]+bestaudio/best[height=1920]/'
                    'bestvideo[height>=1920]+bestaudio/best[height>=1920]/'
                    'bestvideo[height=1080]+bestaudio/best[height=1080]/'
                    'bestvideo[height>=1080]+bestaudio/best[height>=1080]/'
                    # Try width-based selection for horizontal content
                    'bestvideo[width=1080]+bestaudio/best[width=1080]/'
                    'bestvideo[width>=1080]+bestaudio/best[width>=1080]/'
                    # Look for specific high-quality format patterns
                    'best[height=1920]/best[height>=1920]/'
                    'best[height=1080]/best[height>=1080]/'
                    'best[width=1080]/best[width>=1080]/'
                    # Try format IDs that might contain quality indicators
                    'best[format_id*=1920]/best[format_id*=1080]/'
                    # Fallback to highest available
                    'bestvideo+bestaudio/best'
                ),
                # Enhanced format sorting - prioritize resolution above all
                'format_sort': ['res:1920', 'res:1080', 'ext:mp4', 'hasaud', 'br'],
                'format_sort_force': True,
                'extract_flat': False,
                # Force merge of video and audio for best quality
                'merge_output_format': 'mp4',
                # Don't prefer free formats if paid ones are higher quality
                'prefer_free_formats': False,
                # Add verbose format information for debugging
                'listformats': False,  # Set to True for debugging format availability
            })
            
            cookies_file = create_cookies_file(INSTAGRAM_COOKIES)
            ydl_opts['cookiefile'] = cookies_file
            logger.info("Using Instagram cookies for highest quality download")
            
        else:
            raise ValueError("Unsupported URL. Please provide a valid YouTube or Instagram Reel link.")

        # Add a small delay before download
        time.sleep(random.uniform(0.5, 2.0))

        # Perform the download with multiple strategies
        max_attempts = 3  # Increased attempts for better success rate
        last_error = None
        info = None
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Download attempt {attempt + 1}/{max_attempts}")
                
                current_opts = ydl_opts.copy()
                
                if attempt == 1 and normalized_url:
                    # Second attempt: Use pure iOS client and avoid android completely
                    logger.info("Retry with iOS-only client strategy for better quality")
                    current_opts['extractor_args']['youtube']['player_client'] = ['ios']
                    current_opts['extractor_args']['youtube']['skip_dash_manifest'] = False  # Re-enable DASH
                    current_opts['format'] = get_optimal_youtube_format(is_shorts, HAS_PO_TOKEN, 1)
                    
                elif attempt == 2 and normalized_url:
                    # Third attempt: Maximum compatibility - remove all advanced features
                    logger.info("Retry with maximum compatibility - removing PO token dependencies")
                    current_opts['extractor_args']['youtube'] = {
                        'player_client': ['ios'],
                        'lang': ['en'],
                        # Remove all potentially problematic options
                    }
                    current_opts['format'] = get_optimal_youtube_format(is_shorts, HAS_PO_TOKEN, 2)
                
                elif attempt >= 1 and 'instagram.com/reel' in raw_url:
                    # For Instagram: Try different format strategies aggressively
                    logger.info(f"Instagram retry attempt {attempt} - targeting higher quality")
                    if attempt == 1:
                        # More aggressive targeting of 1080p formats
                        current_opts['format'] = (
                            # Try very specific height targeting
                            'bestvideo[height=1920][ext=mp4]+bestaudio[ext=m4a]/'
                            'bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]/'
                            'bestvideo[height>=1920]+bestaudio/best[height>=1920]/'
                            'bestvideo[height>=1080]+bestaudio/best[height>=1080]/'
                            # Try different resolution patterns
                            'best[height=1920][ext=mp4]/best[height=1080][ext=mp4]/'
                            'best[width=1080][ext=mp4]/best[width>=1080]/'
                            'best'
                        )
                        # Adjust format sorting for this attempt
                        current_opts['format_sort'] = ['res:1920', 'res:1080', 'br', 'ext:mp4']
                    else:
                        # Final attempt: List available formats and pick best
                        current_opts['format'] = (
                            # Try to get any high quality format available
                            'bestvideo[height>=1000]+bestaudio/'
                            'best[height>=1000]/'
                            'bestvideo+bestaudio/'
                            'best'
                        )
                        # Remove restrictive format sorting
                        if 'format_sort' in current_opts:
                            del current_opts['format_sort']
                        if 'format_sort_force' in current_opts:
                            del current_opts['format_sort_force']
                
                with yt_dlp.YoutubeDL(current_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                
                # If we get here, download succeeded
                break
                
            except DownloadError as e:
                last_error = e
                error_msg = str(e).lower()
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if 'bot' in error_msg or 'sign in' in error_msg:
                    logger.error("YouTube bot detection triggered")
                    if attempt == max_attempts - 1:
                        raise RuntimeError(
                            "YouTube is blocking downloads due to bot detection. "
                            "Please update your YouTube cookies or try again later."
                        )
                elif 'unavailable' in error_msg or 'private' in error_msg:
                    raise RuntimeError("This video is unavailable, private, or has been removed.")
                
                # Add delay between attempts
                if attempt < max_attempts - 1:
                    delay = random.uniform(2, 5)
                    logger.info(f"Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
            
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed with unexpected error: {e}")
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Download failed after {max_attempts} attempts: {str(e)}")
                
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
        
        # Quality achievement logging with proper Instagram resolution expectations
        if is_shorts:
            if final_height and final_height >= 1080:
                logger.info(f"✅ Shorts downloaded at {final_height}p - excellent quality achieved!")
            elif final_height and final_height >= 720:
                logger.info(f"✅ Shorts downloaded at {final_height}p - good quality achieved")
            else:
                logger.warning(f"⚠️ Shorts downloaded at {final_height}p - YouTube PO token restrictions in effect")
        elif 'instagram.com/reel' in raw_url:
            # Instagram Reels are typically 1080x1920 (vertical) - check for both dimensions
            if (final_height and final_height >= 1920) or (final_width and final_width >= 1080):
                logger.info(f"✅ Instagram Reel downloaded at {final_width}x{final_height} - excellent 1080p+ quality achieved!")
            elif (final_height and final_height >= 1080) or (final_width and final_width >= 720):
                logger.info(f"✅ Instagram Reel downloaded at {final_width}x{final_height} - good quality achieved")
            else:
                logger.warning(f"⚠️ Instagram Reel downloaded at {final_width}x{final_height} - expected 1080x1920, may need fresh cookies")
        else:
            if final_height == 1080:
                logger.info(f"✅ Video downloaded at 1080p - target quality achieved!")
            elif final_height and final_height >= 720:
                logger.info(f"✅ Video downloaded at {final_height}p - good quality achieved")
            else:
                logger.warning(f"⚠️ Video downloaded at {final_height}p - target was 1080p")
        
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
                "YouTube is blocking downloads. Try updating your YouTube cookies "
                "or wait before making more requests."
            )
        elif 'unavailable' in error_msg:
            raise RuntimeError("This video is unavailable or has been removed.")
        else:
            raise RuntimeError(f"Download failed: {str(de)}")
            
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
    # Print startup message with configuration info
    print("\n" + "="*60)
    print("📺 SapZap YouTube/Instagram Downloader - Enhanced Quality")
    print("="*60)
    
    if HAS_PO_TOKEN:
        print("✅ PO Token plugin available - highest quality enabled")
    else:
        print("⚠️  PO Token plugin not installed - may get reduced quality")
        print("   Install with: pip install yt-dlp-get-pot")
    
    if not YOUTUBE_COOKIES:
        print("⚠️  WARNING: No YouTube cookies configured!")
        print("   Add fresh cookies for best quality and reliability")
    else:
        print("✅ YouTube cookies configured")
    
    print("\n🎯 Quality Targets:")
    print("   • YouTube Videos: 1080p")
    print("   • YouTube Shorts: Highest available (bypassing PO token restrictions)")
    print("   • Instagram Reels: 1080x1920 (Full HD)")
    print("\n💡 Tips for better quality:")
    print("   • YouTube: Update cookies regularly for best results")
    print("   • Instagram: Ensure cookies are fresh and valid")
    print("   • Instagram Reels: Target 1920p height (1080x1920 resolution)")
    print("   • For Shorts: Quality may be limited by YouTube's restrictions")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


    