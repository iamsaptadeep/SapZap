import streamlit as st
import requests
import zipfile
import io
import time
import os
import tempfile
import hashlib
from urllib.parse import unquote, urlparse
import yt_dlp
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ClientLoginRequired,
    ChallengeRequired,
    SentryBlock,
    FeedbackRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
    PrivateAccount,
    UserNotFound,
    MediaNotFound,
    ClientError,
)

PAGE_SIZE = 12

st.set_page_config(
    page_title="SapZap",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', -apple-system, sans-serif;
    -webkit-text-size-adjust: 100%;
    touch-action: manipulation;
  }

  .block-container {
    padding: 0.5rem 0.75rem 4rem !important;
    max-width: 500px !important;
    margin: auto !important;
  }

  #MainMenu, footer, header { visibility: hidden; }
  .stDeployButton { display: none; }

  .topbar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 0 16px;
    border-bottom: 1px solid #272727;
    margin-bottom: 16px;
  }
  .topbar h1 {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
    color: #ff0000;
  }

  .post-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border: 1px solid #272727;
    border-bottom: none;
    border-radius: 12px 12px 0 0;
    background: #212121;
  }
  .post-username {
    font-size: 0.85rem;
    font-weight: 600;
    color: #f1f1f1;
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .post-badge {
    flex-shrink: 0;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    border-radius: 4px;
    padding: 3px 8px;
  }
  .badge-photo  { background: #1a2a3a; color: #7ab3e0; }
  .badge-video  { background: #1a1a1a; color: #aaa; }
  .badge-reel   { background: #2a0a0a; color: #ff6666; }
  .badge-album  { background: #2a2200; color: #ccaa55; }
  .badge-story  { background: #2a0a0a; color: #ff6666; }

  .post-caption {
    padding: 8px 12px 12px;
    font-size: 0.8rem;
    color: #aaa;
    line-height: 1.5;
    border: 1px solid #272727;
    border-top: 1px solid #1a1a1a;
    border-radius: 0 0 12px 12px;
    word-break: break-word;
    overflow-wrap: break-word;
    margin-bottom: 8px;
    background: #212121;
  }

  .reel-wrap {
    background: #000;
    width: 100%;
    aspect-ratio: 9/16;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .reel-wrap video { width: 100%; height: 100%; object-fit: contain; }

  .carousel-counter {
    text-align: center;
    color: #666;
    font-size: 0.78rem;
    padding: 6px 0;
    background: #212121;
  }

  .stDownloadButton > button {
    width: 100% !important;
    background: #1db954 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    padding: 11px 16px !important;
    min-height: 44px !important;
  }
  .stDownloadButton > button:hover { background: #179443 !important; }

  .stButton > button[kind="primary"],
  [data-testid="baseButton-primary"] {
    background: #ff0000 !important;
    color: #fff !important;
    border: none !important;
  }
  .stButton > button[kind="primary"]:hover,
  [data-testid="baseButton-primary"]:hover {
    background: #cc0000 !important;
  }

  .stButton > button,
  [data-testid^="baseButton"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100% !important;
    min-height: 44px !important;
    font-size: 0.9rem !important;
  }

  .stButton > button[kind="secondary"],
  [data-testid="baseButton-secondary"] {
    background: #272727 !important;
    color: #aaa !important;
    border: 1px solid #303030 !important;
  }

  [data-testid="stHorizontalBlock"] { gap: 6px !important; }
  .load-more-wrap { margin: 4px 0 20px; }

  .stTextInput input {
    border-radius: 8px !important;
    font-size: 1rem !important;
    min-height: 44px !important;
    padding: 10px 14px !important;
    background: #121212 !important;
    color: #f1f1f1 !important;
    border: 1px solid #303030 !important;
  }
  .stTextInput input:focus {
    border-color: #ff0000 !important;
    box-shadow: 0 0 0 2px rgba(255,0,0,0.15) !important;
  }

  hr { border-color: #272727 !important; margin: 8px 0 14px !important; }
  .stAlert { border-radius: 8px !important; font-size: 0.85rem !important; }

  .res-badge {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 700;
    background: #272727;
    color: #aaa;
    border-radius: 4px;
    padding: 1px 5px;
    margin-left: 4px;
    vertical-align: middle;
  }

  .section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #555;
    margin: 0 0 10px;
  }

  .auth-notice {
    background: #1a1000;
    border: 1px solid #3a2800;
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 0.83rem;
    color: #ccaa55;
    margin: 8px 0 12px;
  }

  .story-meta {
    padding: 6px 12px 10px;
    font-size: 0.75rem;
    color: #555;
    border: 1px solid #272727;
    border-top: 1px solid #1a1a1a;
    border-radius: 0 0 12px 12px;
    background: #212121;
    margin-bottom: 8px;
  }

  .yt-card {
    border: 1px solid #272727;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 14px;
    background: #212121;
  }
  .yt-title {
    padding: 12px 12px 4px;
    font-size: 0.92rem;
    font-weight: 600;
    color: #f1f1f1;
    line-height: 1.4;
  }
  .yt-meta {
    padding: 4px 12px 12px;
    font-size: 0.78rem;
    color: #666;
  }

  .stProgress > div > div > div { background: #ff0000 !important; }
  .stApp { background: #0f0f0f !important; }
</style>
""", unsafe_allow_html=True)


# ── Client Management ─────────────────────────────────────────────────────────

def _clean_session_id(raw_sid: str) -> str:
    """Decode URL-encoded %3A characters and strip quotes/spaces from sessionid."""
    if not raw_sid:
        return ""
    cleaned = unquote(raw_sid.strip().strip('"').strip("'"))
    if "sessionid=" in cleaned:
        cleaned = cleaned.split("sessionid=")[-1].split(";")[0].strip()
    return cleaned


def _default_session_id() -> str:
    try:
        val = st.secrets.get("IG_SESSIONID", "")
        if val:
            return _clean_session_id(str(val))
    except Exception:
        pass
    return _clean_session_id(os.environ.get("IG_SESSIONID", ""))


def _settings_path(session_id: str) -> str:
    digest = hashlib.sha256(session_id.encode()).hexdigest()[:16]
    return os.path.join(tempfile.gettempdir(), f"sapzap_ig_{digest}.json")


def _stable_device(session_id: str) -> dict:
    seed = hashlib.sha256(("sapzap:" + session_id).encode()).hexdigest()

    def uid(n):
        h = hashlib.sha256(f"{seed}:{n}".encode()).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    return {
        "uuids": {
            "phone_id": uid("phone"),
            "uuid": uid("uuid"),
            "client_session_id": uid("session"),
            "advertising_id": uid("ad"),
            "device_id": "android-" + seed[:16],
        },
        "device_settings": {
            "app_version": "269.0.0.18.75",
            "android_version": 26,
            "android_release": "8.0.0",
            "dpi": "480dpi",
            "resolution": "1080x1920",
            "manufacturer": "Samsung",
            "device": "SM-G973F",
            "model": "beyond1",
            "cpu": "exynos9820",
            "version_code": "314665256",
        },
        "user_agent": (
            "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; "
            "Samsung; SM-G973F; beyond1; exynos9820; en_US; 314665256)"
        ),
        "country": "US",
        "locale": "en_US",
    }


@st.cache_resource(show_spinner=False)
def _make_auth_client(session_id: str) -> Client:
    cl = Client()
    cl.delay_range = [1, 3]
    path = _settings_path(session_id)
    try:
        if os.path.exists(path):
            cl.load_settings(path)
        else:
            cl.set_settings(_stable_device(session_id))
    except Exception:
        cl.set_settings(_stable_device(session_id))

    cl.login_by_sessionid(session_id)

    try:
        cl.set_locale("en_US")
        cl.set_country("US")
        cl.dump_settings(path)
    except Exception:
        pass
    return cl


@st.cache_resource(show_spinner=False)
def _make_anon_client() -> Client:
    cl = Client()
    cl.delay_range = [1, 2]
    return cl


def get_cl() -> tuple[Client, bool]:
    sid = _clean_session_id(st.session_state.get("session_id", "")) or _default_session_id()
    if sid:
        try:
            return _make_auth_client(sid), True
        except Exception as e:
            st.session_state["auth_init_error"] = str(e)
    return _make_anon_client(), False


def explain_error(e: Exception) -> str:
    s = str(e)
    if isinstance(e, ChallengeRequired):
        return (
            "Instagram flagged this session with a security challenge. Open "
            "instagram.com in your browser, approve the login attempt, and paste a fresh sessionid."
        )
    if isinstance(e, SentryBlock):
        return "Instagram blocked automated access on this account/IP (SentryBlock). Try another sessionid."
    if isinstance(e, FeedbackRequired):
        return "Instagram rate-limited this action (feedback_required). Wait 5–10 minutes."
    if isinstance(e, (PleaseWaitFewMinutes, RateLimitError)):
        return "Instagram rate limit hit. Wait 3–5 minutes and try again."
    if isinstance(e, PrivateAccount):
        return "This is a private account. Use a Session ID from an account that follows it."
    if isinstance(e, UserNotFound):
        return "No Instagram account exists with that username."
    if isinstance(e, MediaNotFound):
        return "Media not found — it may have been deleted or belongs to a private account."
    low = s.lower()
    if "wait a few minutes" in low or "please wait" in low or "429" in low:
        return "Instagram rate limit hit. Wait 3–5 minutes and try again."
    if "login_required" in low or "login required" in low or "keyerror: 'data'" in low:
        return "Instagram blocked anonymous access. Please add a valid Session ID in the Session ID panel above."
    return f"Request error: {s}"


def handle_session_expiry():
    _make_auth_client.clear()
    st.session_state.pop("session_id", None)
    st.error("Your Instagram Session ID expired or was logged out. Please paste a fresh sessionid.")


def reset_ig_state():
    keys = [
        "ig_resolved_username", "ig_uid", "ig_user",
        "ig_feed_data", "ig_reels_data", "ig_stories_data", "ig_highlights_data",
        "ig_feed_cursor", "ig_feed_has_more",
        "ig_posts_amount", "ig_reels_amount",
        "ig_posts_has_more", "ig_reels_has_more",
        "ig_post_url", "ig_story_url", "bulk_zip_bytes",
    ]
    for k in keys:
        st.session_state.pop(k, None)
    for k in list(st.session_state.keys()):
        if k.startswith(("full_media_", "carousel_", "dlbytes_", "rawvv_", "hl_items_")):
            del st.session_state[k]


# ── API Call & Private V1 Wrappers ────────────────────────────────────────────

def api_call(fn, *args, retries=2, base_wait=5, **kwargs):
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except (LoginRequired, ClientLoginRequired, ChallengeRequired,
                SentryBlock, FeedbackRequired, UserNotFound, PrivateAccount, MediaNotFound):
            raise
        except (PleaseWaitFewMinutes, RateLimitError):
            if attempt < retries - 1:
                time.sleep(base_wait * (attempt + 1))
            else:
                raise
        except Exception as e:
            msg = str(e).lower()
            is_rate = any(k in msg for k in ["wait a few minutes", "429", "please wait", "too many"])
            if is_rate and attempt < retries - 1:
                time.sleep(base_wait * (attempt + 1))
            else:
                raise


def safe_user_info(cl: Client, uname: str, is_auth: bool):
    """Bypass broken public GQL when authenticated by calling _v1 directly."""
    if is_auth:
        try:
            return api_call(cl.user_info_by_username_v1, uname)
        except (LoginRequired, ClientLoginRequired, ChallengeRequired, UserNotFound):
            raise
        except Exception:
            pass
    return api_call(cl.user_info_by_username, uname)


def safe_user_medias_paginated(cl: Client, uid, amount: int, end_cursor: str, is_auth: bool):
    """Use mobile v1 paginated feed first when authenticated to prevent 400 Bad Request."""
    if is_auth:
        try:
            return api_call(cl.user_medias_paginated_v1, uid, amount=amount, end_cursor=end_cursor)
        except (LoginRequired, ClientLoginRequired, ChallengeRequired):
            raise
        except Exception:
            pass
    return api_call(cl.user_medias_paginated, uid, amount=amount, end_cursor=end_cursor)


# ── Media & Network Helpers ───────────────────────────────────────────────────

@st.cache_data(ttl=1800, max_entries=60, show_spinner=False)
def fetch_bytes(url: str, retries: int = 2) -> bytes:
    """Cached byte fetcher with Instagram-compatible headers."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        ),
        "Referer": "https://www.instagram.com/",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    last_err = None
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=45, headers=headers)
            r.raise_for_status()
            return r.content
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(1.5)
    raise last_err


def display_ig_image(url: str):
    """Fetch image bytes server-side so browser CORS/Referer checks never break thumbnails."""
    if not url:
        st.caption("Image unavailable.")
        return
    try:
        img_bytes = fetch_bytes(url)
        st.image(img_bytes, use_container_width=True)
    except Exception:
        st.image(url, use_container_width=True)


def best_image_url(media) -> str:
    try:
        iv2 = getattr(media, "image_versions2", None)
        if iv2 is not None:
            candidates = getattr(iv2, "candidates", None)
            if candidates is None and isinstance(iv2, dict):
                candidates = iv2.get("candidates", [])
            if candidates:
                if hasattr(candidates[0], "url"):
                    return str(sorted(candidates, key=lambda x: getattr(x, "width", 0), reverse=True)[0].url)
                return str(sorted(candidates, key=lambda x: x.get("width", 0), reverse=True)[0]["url"])
    except Exception:
        pass
    if getattr(media, "thumbnail_url", None):
        return str(media.thumbnail_url)
    return ""


def all_video_versions(media) -> list:
    try:
        versions = getattr(media, "video_versions", None) or []
        if not versions:
            url = str(getattr(media, "video_url", "") or "")
            return [(url, "HD", "video_HD.mp4")] if url else []

        def sort_key(v):
            w = getattr(v, "width", 0) if hasattr(v, "width") else v.get("width", 0)
            h = getattr(v, "height", 0) if hasattr(v, "height") else v.get("height", 0)
            return (max(w or 0, h or 0), (w or 0) * (h or 0))

        sorted_v = sorted(versions, key=sort_key, reverse=True)
        seen, result = set(), []
        for v in sorted_v:
            w = getattr(v, "width", 0) if hasattr(v, "width") else v.get("width", 0)
            h = getattr(v, "height", 0) if hasattr(v, "height") else v.get("height", 0)
            url = str(getattr(v, "url", "") if hasattr(v, "url") else v.get("url", ""))
            if not url:
                continue
            label = f"{w}x{h}" if (w and h) else "HD"
            if label in seen:
                continue
            seen.add(label)
            fname = f"video_{w}x{h}.mp4" if (w and h) else "video.mp4"
            result.append((url, label, fname))
        return result
    except Exception:
        url = str(getattr(media, "video_url", "") or "")
        return [(url, "HD", "video_HD.mp4")] if url else []


def best_video_url(media) -> tuple:
    versions = all_video_versions(media)
    return (versions[0][0], versions[0][1]) if versions else ("", "HD")


def video_items_from_raw(raw_versions: list) -> list:
    out, seen = [], set()

    def res(v):
        return int(v.get("width") or 0), int(v.get("height") or 0)

    for v in sorted(raw_versions, key=lambda v: (max(res(v)), res(v)[0] * res(v)[1]), reverse=True):
        w, h = res(v)
        url = str(v.get("url") or "")
        if not url:
            continue
        label = f"{w}x{h}" if (w and h) else "HD"
        if label in seen:
            continue
        seen.add(label)
        fname = f"video_{w}x{h}.mp4" if (w and h) else "video.mp4"
        out.append((url, label, fname))
    return out


def fetch_raw_video_versions(cl: Client, pk) -> list:
    key = f"rawvv_{pk}"
    if key in st.session_state:
        return st.session_state[key]
    versions = []
    try:
        result = api_call(cl.private_request, f"media/{pk}/info/")
        items = (result or {}).get("items") or []
        if items:
            versions = items[0].get("video_versions") or []
    except Exception:
        versions = []
    st.session_state[key] = versions
    return versions


def fetch_media_best(cl: Client, pk, is_auth: bool):
    if is_auth:
        try:
            return api_call(cl.media_info_v1, pk)
        except (LoginRequired, ClientLoginRequired, ChallengeRequired, SentryBlock, FeedbackRequired):
            raise
        except Exception:
            pass
    return api_call(cl.media_info, pk)


def media_type_label(media) -> tuple:
    t = media.media_type
    pt = (getattr(media, "product_type", "") or "").lower()
    if t == 1:
        return "Photo", "badge-photo"
    if t == 2:
        if "reel" in pt or "clips" in pt:
            return "Reel", "badge-reel"
        return "Video", "badge-video"
    if t == 8:
        return f"Album {len(media.resources)}", "badge-album"
    return "Post", "badge-photo"


def is_reel(media) -> bool:
    pt = (getattr(media, "product_type", "") or "").lower()
    return media.media_type == 2 and ("reel" in pt or "clips" in pt)


def make_zip(items: list) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for _lbl, url, filename, _rl in items:
            try:
                zf.writestr(filename, fetch_bytes(url))
            except Exception:
                pass
    buf.seek(0)
    return buf.read()


def make_bulk_profile_zip(medias: list) -> bytes:
    """Package all currently loaded posts/reels into a single ZIP archive."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for media in medias:
            pk = media.pk
            if media.media_type == 2:
                vurl, _ = best_video_url(media)
                if vurl:
                    try:
                        zf.writestr(f"{pk}.mp4", fetch_bytes(vurl))
                    except Exception:
                        pass
            elif media.media_type == 8:
                for idx, res in enumerate(media.resources, start=1):
                    if res.media_type == 2:
                        vurl, _ = best_video_url(res)
                        if vurl:
                            try:
                                zf.writestr(f"{pk}_{idx}.mp4", fetch_bytes(vurl))
                            except Exception:
                                pass
                    else:
                        iurl = best_image_url(res)
                        if iurl:
                            try:
                                zf.writestr(f"{pk}_{idx}.jpg", fetch_bytes(iurl))
                            except Exception:
                                pass
            else:
                iurl = best_image_url(media)
                if iurl:
                    try:
                        zf.writestr(f"{pk}.jpg", fetch_bytes(iurl))
                    except Exception:
                        pass
    buf.seek(0)
    return buf.read()


def render_lazy_download(label: str, url: str, file_name: str, mime: str, key: str):
    """
    CRITICAL FIX: Two-step On-Demand Download.
    Prevents Streamlit from downloading 20+ videos into RAM simultaneously on page render.
    """
    cache_key = f"dlbytes_{key}"
    if cache_key not in st.session_state:
        if st.button(f"Prepare {label}", key=f"prep_{key}", use_container_width=True):
            with st.spinner(f"Fetching {label}..."):
                try:
                    st.session_state[cache_key] = fetch_bytes(url)
                    st.rerun()
                except Exception as e:
                    st.error(f"Download failed: {e}")
    else:
        st.download_button(
            label=f"⬇ Save {label}",
            data=st.session_state[cache_key],
            file_name=file_name,
            mime=mime,
            key=f"save_{key}",
            use_container_width=True,
        )


# ── Input Detection ───────────────────────────────────────────────────────────

def detect_input_type(text: str) -> str:
    t = text.strip()
    if "instagram.com" in t or "instagr.am" in t:
        if "/stories/" in t:
            return "story_url"
        if any(seg in t for seg in ("/p/", "/reel/", "/reels/", "/tv/", "/share/")):
            return "post_url"
        return "profile_url"
    if t:
        return "username"
    return "unknown"


def extract_username_from_url(url: str) -> str:
    """Cleanly strip query params (?igsh=...) and extract the Instagram handle."""
    parsed = urlparse(url.strip())
    path = parsed.path.strip("/")
    parts = [p for p in path.split("/") if p]
    skip = {"p", "reel", "reels", "tv", "stories", "explore", "accounts", "share"}
    for part in parts:
        if part.lower() not in skip:
            return part.lstrip("@")
    return ""


# ── Carousel & Download Renderers ─────────────────────────────────────────────

def render_carousel(media, key: str):
    resources = media.resources
    n = len(resources)
    if n == 0:
        st.caption("No items in album.")
        return
    sk = f"carousel_{key}"
    if sk not in st.session_state:
        st.session_state[sk] = 0
    idx = min(st.session_state[sk], n - 1)
    res = resources[idx]

    if res.media_type == 2:
        vurl, _ = best_video_url(res)
        if vurl:
            st.video(vurl)
        else:
            st.caption("Video unavailable.")
    else:
        img_url = best_image_url(res)
        display_ig_image(img_url)

    st.markdown(f'<div class="carousel-counter">{idx + 1} / {n}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Prev", key=f"prev_{key}", disabled=(idx == 0), use_container_width=True):
            st.session_state[sk] = max(0, idx - 1)
            st.rerun()
    with c2:
        if st.button("Next", key=f"next_{key}", disabled=(idx == n - 1), use_container_width=True):
            st.session_state[sk] = min(n - 1, idx + 1)
            st.rerun()


def render_download_buttons(media, all_items: list, key: str,
                             is_reel_mode: bool = False, cl: Client = None, is_auth: bool = False):
    if not all_items:
        st.caption("No downloadable media found.")
        return

    if is_reel_mode or media.media_type == 2:
        raw_vv = st.session_state.get(f"rawvv_{media.pk}")
        if raw_vv:
            items = video_items_from_raw(raw_vv)
            if items:
                all_items = [(f"Video ({rl})", url, fn, rl) for url, rl, fn in items]

        if cl and is_auth and raw_vv is None:
            if st.button("Check 1080p / Max Quality", key=f"fhd_btn_{key}", type="secondary", use_container_width=True):
                with st.spinner("Checking resolution ladder..."):
                    vv = fetch_raw_video_versions(cl, media.pk)
                if vv:
                    st.toast(f"Found {len(video_items_from_raw(vv))} resolution options!")
                else:
                    st.toast("Using default stream.")
                st.rerun()

        best_lbl, best_url, best_fn, best_rl = all_items[0]
        label_str = f"Video {best_rl}" if best_rl else "Video"
        render_lazy_download(
            label=label_str,
            url=best_url,
            file_name=f"{media.pk}_{best_fn}",
            mime="video/mp4",
            key=f"{key}_best",
        )

        if len(all_items) > 1:
            with st.expander("More resolutions"):
                for i, (_lbl, url, fname, rlabel) in enumerate(all_items[1:], start=1):
                    render_lazy_download(
                        label=f"Video {rlabel}",
                        url=url,
                        file_name=f"{media.pk}_{fname}",
                        mime="video/mp4",
                        key=f"{key}_res{i}",
                    )

    elif len(all_items) == 1:
        lbl, url, fname, rlabel = all_items[0]
        res_info = f" ({rlabel})" if rlabel else ""
        render_lazy_download(
            label=f"{lbl}{res_info}",
            url=url,
            file_name=f"{media.pk}_{fname}",
            mime="video/mp4" if fname.endswith(".mp4") else "image/jpeg",
            key=f"{key}_single",
        )

    else:
        cols = st.columns(2)
        for i, (lbl, url, fname, _rlabel) in enumerate(all_items):
            with cols[i % 2]:
                render_lazy_download(
                    label=lbl,
                    url=url,
                    file_name=f"{media.pk}_{fname}",
                    mime="video/mp4" if fname.endswith(".mp4") else "image/jpeg",
                    key=f"{key}_album_{i}",
                )

        zip_cache_key = f"dlbytes_{media.pk}_zip"
        if zip_cache_key not in st.session_state:
            if st.button(f"Prepare Album ZIP ({len(all_items)} items)", key=f"prep_zip_{key}", use_container_width=True):
                with st.spinner("Building Album ZIP..."):
                    st.session_state[zip_cache_key] = make_zip(all_items)
                    st.rerun()
        else:
            st.download_button(
                "⬇ Save Album ZIP",
                data=st.session_state[zip_cache_key],
                file_name=f"{media.pk}_album.zip",
                mime="application/zip",
                key=f"dl_{key}_zip",
                use_container_width=True,
            )


# ── Post & Story Cards ────────────────────────────────────────────────────────

def render_post(media, idx: int, show_reel_aspect: bool = False, cl: Client = None, is_auth: bool = False):
    key = f"post_{idx}_{media.pk}"
    is_vid = media.media_type == 2
    label, badge_cls = media_type_label(media)
    username = media.user.username if getattr(media, "user", None) else "unknown"
    caption = getattr(media, "caption_text", "") or ""

    raw_vv = st.session_state.get(f"rawvv_{media.pk}")

    if is_vid:
        if raw_vv:
            items = video_items_from_raw(raw_vv)
            all_items = [(f"Video {rl}", url, fn, rl) for url, rl, fn in items]
        else:
            all_items = [(f"Video {rl}", url, fn, rl) for url, rl, fn in all_video_versions(media)]
    elif media.media_type == 8:
        all_items = []
        for i, res in enumerate(media.resources):
            if res.media_type == 2:
                v_list = all_video_versions(res)
                if v_list:
                    url, rl, fn = v_list[0]
                    all_items.append((f"Video {i + 1}", url, f"v{i + 1}_{fn}", rl))
            else:
                img_url = best_image_url(res)
                if img_url:
                    all_items.append((f"Photo {i + 1}", img_url, f"photo_{i + 1}.jpg", ""))
    else:
        img_url = best_image_url(media)
        all_items = [("Photo", img_url, "photo.jpg", "")] if img_url else []

    st.markdown(
        f'<div class="post-header">'
        f'<span class="post-username">@{username}</span>'
        f'<span class="post-badge {badge_cls}">{label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if media.media_type == 8:
        render_carousel(media, key)
    elif is_vid:
        vurl = all_items[0][1] if all_items else str(getattr(media, "video_url", "") or "")
        res_label = all_items[0][3] if all_items else ""
        if vurl:
            if show_reel_aspect:
                st.markdown('<div class="reel-wrap">', unsafe_allow_html=True)
            st.video(vurl)
            if show_reel_aspect:
                st.markdown('</div>', unsafe_allow_html=True)
            if res_label and res_label != "HD":
                st.markdown(
                    f'<div style="text-align:right;padding:2px 10px 6px">'
                    f'<span class="res-badge">{res_label}</span></div>',
                    unsafe_allow_html=True,
                )
    else:
        img_url = best_image_url(media)
        display_ig_image(img_url)

    if caption:
        short = caption[:140] + ("..." if len(caption) > 140 else "")
        st.markdown(f'<div class="post-caption">{short}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

    render_download_buttons(
        media, all_items, key,
        is_reel_mode=(show_reel_aspect and is_vid),
        cl=cl,
        is_auth=is_auth,
    )
    st.markdown("---")


def render_story(story, idx):
    key = f"story_{idx}_{story.pk}"
    is_vid = story.media_type == 2

    st.markdown(
        f'<div class="post-header">'
        f'<span class="post-username">Story</span>'
        f'<span class="post-badge badge-story">Story</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if is_vid:
        vurl, _ = best_video_url(story)
        if vurl:
            st.video(vurl)
        else:
            st.caption("Video unavailable.")
    else:
        img_url = best_image_url(story)
        display_ig_image(img_url)

    taken_at = getattr(story, "taken_at", None)
    ts = taken_at.strftime("%b %d, %Y  %H:%M") if taken_at else ""
    st.markdown(f'<div class="story-meta">{ts}</div>', unsafe_allow_html=True)

    if is_vid:
        versions = all_video_versions(story)
        if versions:
            url, label, fname = versions[0]
            render_lazy_download(
                label=f"Story Video ({label})",
                url=url,
                file_name=f"story_{story.pk}_{fname}",
                mime="video/mp4",
                key=f"{key}_vid",
            )
    else:
        img_url = best_image_url(story)
        if img_url:
            render_lazy_download(
                label="Story Photo",
                url=img_url,
                file_name=f"story_{story.pk}.jpg",
                mime="image/jpeg",
                key=f"{key}_img",
            )

    st.markdown("---")


# ── YouTube Downloader ────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _get_ffmpeg_path() -> str | None:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def download_yt_video(url: str) -> tuple:
    ffmpeg = _get_ffmpeg_path()

    with tempfile.TemporaryDirectory() as tmpdir:
        outtmpl = os.path.join(tmpdir, "video.%(ext)s")
        fmt = (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            if ffmpeg else "best[ext=mp4]/best"
        )

        ydl_opts = {
            "format": fmt,
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "extractor_args": {"youtube": {"player_client": ["ios", "android", "web"]}},
        }
        if ffmpeg:
            ydl_opts["ffmpeg_location"] = ffmpeg

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True) or {}

        files = [f for f in os.listdir(tmpdir) if not f.endswith(".part")]
        if not files:
            raise RuntimeError("Download failed: no output file was created.")

        filepath = os.path.join(tmpdir, files[0])
        with open(filepath, "rb") as f:
            data = f.read()

        title = info.get("title", "video")
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()[:80] or "video"
        ext = os.path.splitext(files[0])[1] or ".mp4"
        return data, f"{safe_title}{ext}", info


def _clear_yt_callback():
    """Safe callback to reset YouTube state BEFORE widgets instantiate."""
    st.session_state.pop("yt_data", None)
    st.session_state.pop("yt_filename", None)
    st.session_state.pop("yt_info", None)
    st.session_state["yt_url_input"] = ""


def render_youtube_tab():
    st.markdown('<p class="section-label">YouTube / Shorts Downloader</p>', unsafe_allow_html=True)

    url_input = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/shorts/... or any YouTube link",
        label_visibility="collapsed",
        key="yt_url_input",
    )

    c1, c2 = st.columns([3, 1])
    with c1:
        dl_btn = st.button("Download", type="primary", key="yt_dl_btn", use_container_width=True)
    with c2:
        st.button("Reset", key="yt_reset_btn", type="secondary", on_click=_clear_yt_callback, use_container_width=True)

    if dl_btn and url_input.strip():
        st.session_state.pop("yt_data", None)
        st.session_state.pop("yt_filename", None)
        st.session_state.pop("yt_info", None)
        with st.spinner("Downloading at highest quality..."):
            try:
                data, filename, info = download_yt_video(url_input.strip())
                st.session_state["yt_data"] = data
                st.session_state["yt_filename"] = filename
                st.session_state["yt_info"] = info
            except Exception as e:
                st.error(f"Download failed: {e}")

    yt_data = st.session_state.get("yt_data")
    yt_info = st.session_state.get("yt_info", {})

    if yt_data:
        title = yt_info.get("title", "Video")
        uploader = yt_info.get("uploader") or yt_info.get("channel", "")
        duration = yt_info.get("duration", 0) or 0
        view_count = yt_info.get("view_count", 0) or 0
        width = yt_info.get("width", 0) or 0
        height = yt_info.get("height", 0) or 0

        dur_str = f"{int(duration) // 60}:{int(duration) % 60:02d}" if duration else ""
        res_str = f"{width}x{height}" if (width and height) else "Best quality"
        parts = [p for p in [uploader, res_str, dur_str, f"{view_count:,} views" if view_count else ""] if p]
        meta_str = "  ·  ".join(parts)

        st.markdown(
            f'<div class="yt-card">'
            f'<div class="yt-title">{title}</div>'
            f'<div class="yt-meta">{meta_str}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        thumbnail = yt_info.get("thumbnail", "")
        if thumbnail:
            try:
                st.image(thumbnail, use_container_width=True)
            except Exception:
                pass

        st.download_button(
            "⬇ Save Video",
            data=yt_data,
            file_name=st.session_state.get("yt_filename", "video.mp4"),
            mime="video/mp4",
            key="yt_dl_final",
            use_container_width=True,
        )


# ── Instagram Sections ────────────────────────────────────────────────────────

def render_auth_notice(uname: str = ""):
    who = f"@{uname}" if uname else "This content"
    st.markdown(
        f'<div class="auth-notice">'
        f'<strong>{who}</strong> requires an active Instagram Session ID. '
        f'Open the <strong>Session ID</strong> panel above and paste your <code>sessionid</code> cookie.'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_ig_single_post(url: str, cl: Client, is_auth: bool):
    with st.spinner("Fetching media..."):
        try:
            pk = api_call(cl.media_pk_from_url, url)
            media = fetch_media_best(cl, pk, is_auth)
            if is_auth and media.media_type == 2:
                fetch_raw_video_versions(cl, pk)
        except (LoginRequired, ClientLoginRequired):
            if is_auth:
                handle_session_expiry()
            else:
                render_auth_notice()
            return
        except Exception as e:
            st.error(explain_error(e))
            return
    render_post(media, idx=99999, show_reel_aspect=is_reel(media), cl=cl, is_auth=is_auth)


def render_ig_single_story(url: str, cl: Client, is_auth: bool):
    if not is_auth:
        render_auth_notice()
        st.info("Instagram stories strictly require a logged-in Session ID.")
        return

    with st.spinner("Fetching story..."):
        try:
            pk = api_call(cl.story_pk_from_url, url)
            story = api_call(cl.story_info_v1, pk)
        except (LoginRequired, ClientLoginRequired):
            handle_session_expiry()
            return
        except Exception as e:
            st.error(explain_error(e))
            return
    render_story(story, idx=0)


def render_bulk_zip_bar(medias: list, label_prefix: str, uname: str):
    """Allows downloading all loaded profile posts/reels as a single ZIP at once."""
    if not medias:
        return
    zip_key = f"bulk_zip_bytes_{label_prefix}_{len(medias)}"
    if zip_key not in st.session_state:
        if st.button(
            f"📦 Prepare Bulk ZIP of All {len(medias)} Loaded {label_prefix}",
            key=f"prep_bulk_{label_prefix}",
            type="secondary",
            use_container_width=True,
        ):
            with st.spinner(f"Packaging {len(medias)} items into ZIP..."):
                st.session_state[zip_key] = make_bulk_profile_zip(medias)
                st.rerun()
    else:
        st.download_button(
            label=f"⬇ Save All {len(medias)} {label_prefix} (.ZIP)",
            data=st.session_state[zip_key],
            file_name=f"{uname}_{label_prefix.lower()}_{len(medias)}.zip",
            mime="application/zip",
            key=f"dl_bulk_{label_prefix}",
            use_container_width=True,
        )
    st.markdown("---")


def render_ig_feed(uname: str, uid, cl: Client, is_auth: bool):
    if st.session_state.get("ig_feed_data") is None:
        with st.spinner(f"Loading @{uname}'s posts..."):
            try:
                medias, cursor = safe_user_medias_paginated(cl, uid, PAGE_SIZE, "", is_auth)
                st.session_state["ig_feed_data"] = list(medias or [])
                st.session_state["ig_feed_cursor"] = cursor or ""
                st.session_state["ig_feed_has_more"] = bool(cursor)
            except (LoginRequired, ClientLoginRequired):
                if is_auth:
                    handle_session_expiry()
                else:
                    render_auth_notice(uname)
                return
            except Exception as e:
                st.error(explain_error(e))
                return

    posts = st.session_state.get("ig_feed_data") or []
    if not posts:
        st.info("No posts found for this account.")
        return

    st.markdown(f'<p class="section-label">{len(posts)} posts loaded</p>', unsafe_allow_html=True)
    render_bulk_zip_bar(posts, "Posts", uname)

    for i, media in enumerate(posts):
        try:
            render_post(media, i, show_reel_aspect=False, cl=cl, is_auth=is_auth)
        except Exception as e:
            st.warning(f"Could not render post {i + 1}: {e}")

    if st.session_state.get("ig_feed_has_more", False):
        st.markdown('<div class="load-more-wrap">', unsafe_allow_html=True)
        if st.button(f"Load {PAGE_SIZE} More Posts", use_container_width=True, key="load_more_posts"):
            ok = False
            with st.spinner("Loading more posts..."):
                try:
                    cur = st.session_state.get("ig_feed_cursor", "")
                    medias, new_cur = safe_user_medias_paginated(cl, uid, PAGE_SIZE, cur, is_auth)
                    existing = st.session_state.get("ig_feed_data") or []
                    seen = {m.pk for m in existing}
                    added = [m for m in (medias or []) if m.pk not in seen]
                    st.session_state["ig_feed_data"] = existing + added
                    st.session_state["ig_feed_cursor"] = new_cur or ""
                    st.session_state["ig_feed_has_more"] = bool(new_cur)
                    ok = True
                except Exception as e:
                    st.warning(f"Could not load more posts: {explain_error(e)}")
            if ok:
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def _fetch_clips(cl: Client, uid, amount: int, is_auth: bool) -> list:
    reels = []
    if is_auth:
        try:
            reels = api_call(cl.user_clips_v1, uid, amount=amount)
        except (LoginRequired, ClientLoginRequired, ChallengeRequired):
            raise
        except Exception:
            pass
    if not reels:
        try:
            reels = api_call(cl.user_clips, uid, amount=amount)
        except Exception:
            medias, _ = safe_user_medias_paginated(cl, uid, amount, "", is_auth)
            reels = [m for m in (medias or []) if is_reel(m)]

    seen, uniq = set(), []
    for r in (reels or []):
        if r.pk not in seen:
            uniq.append(r)
            seen.add(r.pk)
    return uniq


def render_ig_reels(uname: str, uid, cl: Client, is_auth: bool):
    if st.session_state.get("ig_reels_data") is None:
        with st.spinner(f"Loading @{uname}'s reels..."):
            try:
                uniq = _fetch_clips(cl, uid, PAGE_SIZE, is_auth)
                st.session_state["ig_reels_data"] = uniq
                st.session_state["ig_reels_amount"] = PAGE_SIZE
                st.session_state["ig_reels_has_more"] = len(uniq) >= PAGE_SIZE
            except (LoginRequired, ClientLoginRequired):
                if is_auth:
                    handle_session_expiry()
                else:
                    render_auth_notice(uname)
                return
            except Exception as e:
                st.error(explain_error(e))
                return

    reels = st.session_state.get("ig_reels_data") or []
    if not reels:
        st.info("No reels found for this account.")
        return

    st.markdown(f'<p class="section-label">{len(reels)} reels loaded</p>', unsafe_allow_html=True)
    render_bulk_zip_bar(reels, "Reels", uname)

    for i, media in enumerate(reels):
        try:
            render_post(media, i + 10000, show_reel_aspect=True, cl=cl, is_auth=is_auth)
        except Exception as e:
            st.warning(f"Could not render reel {i + 1}: {e}")

    if st.session_state.get("ig_reels_has_more", False):
        st.markdown('<div class="load-more-wrap">', unsafe_allow_html=True)
        if st.button(f"Load {PAGE_SIZE} More Reels", use_container_width=True, key="load_more_reels"):
            ok = False
            new_amt = st.session_state.get("ig_reels_amount", PAGE_SIZE) + PAGE_SIZE
            prev_count = len(reels)
            with st.spinner("Loading more reels..."):
                try:
                    uniq = _fetch_clips(cl, uid, new_amt, is_auth)
                    st.session_state["ig_reels_data"] = uniq
                    st.session_state["ig_reels_amount"] = new_amt
                    st.session_state["ig_reels_has_more"] = len(uniq) > prev_count and len(uniq) >= new_amt
                    ok = True
                except Exception as e:
                    st.warning(f"Could not load more reels: {explain_error(e)}")
            if ok:
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def render_ig_stories(uname: str, uid, cl: Client, is_auth: bool):
    if not is_auth:
        render_auth_notice(uname)
        st.info("Stories require a logged-in Session ID.")
        return

    if st.session_state.get("ig_stories_data") is None:
        with st.spinner(f"Loading @{uname}'s stories..."):
            try:
                stories = api_call(cl.user_stories_v1, uid)
                st.session_state["ig_stories_data"] = stories or []
            except (LoginRequired, ClientLoginRequired):
                handle_session_expiry()
                return
            except Exception as e:
                st.error(explain_error(e))
                return

    stories = st.session_state.get("ig_stories_data") or []
    if not stories:
        st.info("No active stories (stories expire after 24 hours).")
        return

    st.markdown(f'<p class="section-label">{len(stories)} active stories</p>', unsafe_allow_html=True)
    for i, story in enumerate(stories):
        try:
            render_story(story, i)
        except Exception as e:
            st.warning(f"Could not render story {i + 1}: {e}")


def render_ig_highlights(uname: str, uid, cl: Client, is_auth: bool):
    if not is_auth:
        render_auth_notice(uname)
        st.info("Highlights require a logged-in Session ID.")
        return

    if st.session_state.get("ig_highlights_data") is None:
        with st.spinner(f"Loading @{uname}'s highlights..."):
            try:
                hls = api_call(cl.user_highlights_v1, uid)
                st.session_state["ig_highlights_data"] = hls or []
            except (LoginRequired, ClientLoginRequired):
                handle_session_expiry()
                return
            except Exception as e:
                st.error(explain_error(e))
                return

    hls = st.session_state.get("ig_highlights_data") or []
    if not hls:
        st.info("No highlights found for this account.")
        return

    st.markdown(f'<p class="section-label">{len(hls)} highlights</p>', unsafe_allow_html=True)
    for h in hls:
        title = getattr(h, "title", "Highlight") or "Highlight"
        count = getattr(h, "media_count", None)
        head = f"{title}  ·  {count} items" if count else title
        with st.expander(head):
            items_key = f"hl_items_{h.pk}"
            if items_key not in st.session_state:
                if st.button("Load Highlight Items", key=f"hl_load_{h.pk}", use_container_width=True):
                    with st.spinner("Loading highlight..."):
                        try:
                            info = api_call(cl.highlight_info_v1, h.pk)
                            st.session_state[items_key] = list(getattr(info, "items", []) or [])
                        except Exception as e:
                            st.error(explain_error(e))
                    st.rerun()
            else:
                items = st.session_state[items_key]
                if not items:
                    st.caption("No items in this highlight.")
                for j, item in enumerate(items):
                    try:
                        render_story(item, f"{h.pk}_{j}")
                    except Exception as e:
                        st.warning(f"Could not render item {j + 1}: {e}")


# ── Instagram Main Tab ────────────────────────────────────────────────────────

def _clear_ig_callback():
    """Safe callback to clear Instagram input state BEFORE widget renders."""
    reset_ig_state()
    st.session_state["ig_raw_input"] = ""


def render_instagram_tab():
    cl, is_auth = get_cl()

    with st.expander("Session ID (Recommended for Full Access)", expanded=not is_auth):
        if is_auth:
            st.caption("✅ Authenticated — Private Mobile API v1 active (1080p, Stories, Highlights & Bulk ZIP enabled).")
        else:
            st.caption("⚪ Anonymous — Public access is heavily rate-limited by Instagram. Add a Session ID for reliable scraping.")
            if st.session_state.get("auth_init_error"):
                st.warning(f"Previous session failed to initialize: {st.session_state['auth_init_error']}")

        session_input = st.text_input(
            "Instagram Session ID",
            type="password",
            placeholder="Paste sessionid cookie value here",
            key="session_id_input",
        )
        cs1, cs2 = st.columns(2)
        with cs1:
            if st.button("Save Session", key="save_session", type="primary"):
                cleaned_sid = _clean_session_id(session_input)
                if cleaned_sid:
                    _make_auth_client.clear()
                    st.session_state.pop("auth_init_error", None)
                    st.session_state["session_id"] = cleaned_sid
                    st.success("Session saved!")
                    st.rerun()
                else:
                    st.error("Session ID cannot be empty.")
        with cs2:
            if st.button("Clear Session", key="clear_session", type="secondary"):
                st.session_state.pop("session_id", None)
                st.session_state.pop("auth_init_error", None)
                _make_auth_client.clear()
                st.rerun()

        if not is_auth:
            st.markdown("""
**How to get your Session ID:**
1. Log into `instagram.com` in Chrome/Edge (use a burner account for safety).
2. Press **F12** → **Application** → **Cookies** → `https://www.instagram.com`.
3. Copy the **Value** of `sessionid` and paste it above.
            """)

    st.markdown("---")

    ig_sub = st.session_state.get("ig_sub_tab", "feed")
    sub_tabs = [("Feed", "feed"), ("Reels", "reels"), ("Stories", "stories"), ("Highlights", "highlights")]
    row1 = st.columns(2)
    row2 = st.columns(2)
    for (label, value), cell in zip(sub_tabs, [row1[0], row1[1], row2[0], row2[1]]):
        with cell:
            if st.button(
                label,
                key=f"sub_{value}",
                type="primary" if ig_sub == value else "secondary",
                use_container_width=True,
            ):
                st.session_state["ig_sub_tab"] = value
                st.rerun()

    placeholder_map = {
        "feed": "Username, profile URL, or post URL",
        "reels": "Username, profile URL, or reel URL",
        "stories": "Username, profile URL, or story URL",
        "highlights": "Username or profile URL",
    }

    raw_input = st.text_input(
        "Input",
        placeholder=placeholder_map.get(ig_sub, "Username or URL"),
        label_visibility="collapsed",
        key="ig_raw_input",
    )

    ci1, ci2 = st.columns([3, 1])
    with ci1:
        fetch_btn = st.button("Fetch", type="primary", key="ig_fetch_btn", use_container_width=True)
    with ci2:
        st.button("Reset", type="secondary", key="ig_reset_btn", on_click=_clear_ig_callback, use_container_width=True)

    if fetch_btn and raw_input.strip():
        text = raw_input.strip()
        if text.startswith("@"):
            text = text[1:]
        input_type = detect_input_type(text)

        reset_ig_state()

        if input_type == "post_url":
            st.session_state["ig_post_url"] = text
        elif input_type == "story_url":
            st.session_state["ig_story_url"] = text
        else:
            uname = extract_username_from_url(text) if input_type == "profile_url" else text.split("?")[0].strip("/")
            if uname:
                st.session_state["ig_resolved_username"] = uname
                st.session_state["ig_posts_amount"] = PAGE_SIZE
                st.session_state["ig_reels_amount"] = PAGE_SIZE
        st.rerun()

    post_url = st.session_state.get("ig_post_url")
    if post_url:
        render_ig_single_post(post_url, cl, is_auth)
        return

    story_url = st.session_state.get("ig_story_url")
    if story_url:
        render_ig_single_story(story_url, cl, is_auth)
        return

    uname = st.session_state.get("ig_resolved_username")
    if not uname:
        return

    if not st.session_state.get("ig_uid"):
        with st.spinner(f"Looking up @{uname}..."):
            try:
                user = safe_user_info(cl, uname, is_auth)
                st.session_state["ig_user"] = user
                st.session_state["ig_uid"] = user.pk
            except (LoginRequired, ClientLoginRequired):
                if is_auth:
                    handle_session_expiry()
                else:
                    render_auth_notice(uname)
                return
            except Exception as e:
                st.error(explain_error(e))
                return

    uid = st.session_state["ig_uid"]
    user = st.session_state.get("ig_user")

    if user:
        c1, c2 = st.columns([1, 4])
        with c1:
            pic = str(user.profile_pic_url) if getattr(user, "profile_pic_url", None) else ""
            if pic:
                try:
                    st.image(fetch_bytes(pic), width=64)
                except Exception:
                    pass
        with c2:
            lock = " 🔒" if getattr(user, "is_private", False) else ""
            st.markdown(f"**@{user.username}**{lock}")
            st.caption(f"{getattr(user, 'media_count', 0):,} posts  ·  {getattr(user, 'follower_count', 0):,} followers")

        if getattr(user, "is_private", False) and not is_auth:
            st.warning(
                "This is a private account. Open the Session ID panel and paste a "
                "sessionid from an account that follows it to view its media."
            )
            return
        st.markdown("---")

    if ig_sub == "feed":
        render_ig_feed(uname, uid, cl, is_auth)
    elif ig_sub == "reels":
        render_ig_reels(uname, uid, cl, is_auth)
    elif ig_sub == "stories":
        render_ig_stories(uname, uid, cl, is_auth)
    elif ig_sub == "highlights":
        render_ig_highlights(uname, uid, cl, is_auth)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="topbar"><h1>SapZap</h1></div>', unsafe_allow_html=True)

main_tab = st.session_state.get("main_tab", "instagram")
mt1, mt2 = st.columns(2)
with mt1:
    if st.button(
        "Instagram",
        key="main_tab_ig",
        type="primary" if main_tab == "instagram" else "secondary",
        use_container_width=True,
    ):
        st.session_state["main_tab"] = "instagram"
        st.rerun()
with mt2:
    if st.button(
        "YouTube",
        key="main_tab_yt",
        type="primary" if main_tab == "youtube" else "secondary",
        use_container_width=True,
    ):
        st.session_state["main_tab"] = "youtube"
        st.rerun()

st.markdown("---")

if main_tab == "instagram":
    render_instagram_tab()
else:
    render_youtube_tab()


    