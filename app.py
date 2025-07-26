import os
import re
import uuid
import tempfile
import shutil
import logging
from flask import Flask, request, render_template, Response
import yt_dlp

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Refresh Instagram cookies periodically via browser login.
INSTAGRAM_COOKIES = {
    'sessionid': '62586856555%3AUrJiGyKV2H6db0%3A7%3AAYdxkb-PFtr2tdKmoM7ecXV3Wltfj08R1ljvQ61GYA',
    'ds_user_id': '62586856555',
    'csrftoken': 'N7J4wem0oKB16aRfi5zX8u',
    'rur': '"HIL\05462586856555\0541785099262:01fe44bdea098b826d993cce284d6b774aaf32384da9b09458a4e1f4c60b78e008390929"'
}

sHORTS_REGEX = re.compile(r'(?:youtube\.com/shorts/|youtu\.be/)([\w-]+)')


def create_instagram_cookies_file():
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tf:
        tf.write("# Netscape HTTP Cookie File\n")
        for name, value in INSTAGRAM_COOKIES.items():
            tf.write(f".instagram.com\tTRUE\t/\tTRUE\t2147483647\t{name}\t{value}\n")
        return tf.name


def clean_filename(title, resolution=None, ext='mp4'):
    if not title:
        base = f"sapzap_{uuid.uuid4().hex[:8]}"
    else:
        clean = re.sub(r'[^\w\s-]', '', title).strip()
        clean = re.sub(r'[-\s]+', '_', clean)
        base = f"sapzap_{clean[:50]}"
    return f"{base}_{resolution}p.{ext}" if resolution else f"{base}.{ext}"


def download_media(original_url):
    raw = original_url.strip()
    url_base = raw.split('?', 1)[0]

    # Detect if this is a Shorts URL
    shorts_m = sHORTS_REGEX.search(raw)
    is_shorts = bool(shorts_m)

    # Extract video ID and form canonical watch URL
    vid_match = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/))([\w-]+)', url_base)
    if vid_match:
        vid = vid_match.group(1)
        logger.info(f"Normalized YouTube URL for ID: {vid}")
        url = f"https://www.youtube.com/watch?v={vid}"
    else:
        url = url_base

    temp_dir = tempfile.mkdtemp()
    cookies_file = None

    ydl_opts = {
        'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': True,
        'noplaylist': True,
        'retries': 5,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'windowsfilenames': True,
        'logger': logger,
        'socket_timeout': 30,
        'noprogress': True,
        'merge_output_format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'en-US,en;q=0.5',
        },
    }

    if 'instagram.com/reel' in url:
        logger.info("Instagram Reel URL detected.")
        ydl_opts['format'] = 'best'
        cookies_file = create_instagram_cookies_file()
        ydl_opts['cookiefile'] = cookies_file

    elif 'youtube.com/watch' in url:
        logger.info("YouTube video URL detected.")
        if is_shorts:
            # Use highest possible resolution for Shorts
            ydl_opts['format'] = 'bestvideo*+bestaudio/best'
        else:
            # Cap standard videos at 1080p
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
        # Use desktop client by default (no mobile extractor args)

    else:
        shutil.rmtree(temp_dir)
        raise ValueError("Unsupported URL. Provide YouTube watch/shorts or Instagram Reel.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        files = [f for f in os.listdir(temp_dir) if f.lower().endswith(('.mp4', '.mkv', '.webm'))]
        if not files:
            raise RuntimeError("Download succeeded but no media found.")
        file_path = os.path.join(temp_dir, files[0])

        title = info.get('title', 'video')
        height = info.get('height') or (info.get('requested_formats')[0].get('height') if info.get('requested_formats') else None)
        filename = clean_filename(title, height)

        return file_path, filename, temp_dir

    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

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
        return "URL is required", 400
    try:
        file_path, filename, temp_dir = download_media(url)
        def generate():
            try:
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(1024*1024), b''):
                        yield chunk
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        ext = os.path.splitext(filename)[1][1:].lower()
        mime = {'mp4': 'video/mp4', 'webm': 'video/webm', 'mkv': 'video/x-matroska'}.get(ext, 'application/octet-stream')
        return Response(generate(), mimetype=mime,
                        headers={'Content-Disposition': f'attachment; filename="{filename}"'})
    except ValueError as ve:
        logger.warning(f"Bad URL {url}: {ve}")
        return str(ve), 400
    except Exception as e:
        logger.error(f"Download failed {url}: {e}")
        return ("An error occurred downloading your video. Please verify the link and try again."), 500


if __name__ == '__main__':
    app.run(debug=False)

