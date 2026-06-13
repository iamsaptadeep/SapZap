import streamlit as st
import requests
import zipfile
import io
import time
import os
import tempfile
from contextlib import nullcontext as contextlib_nullcontext
import yt_dlp
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

PAGE_SIZE = 20

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

  /* Top bar */
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

  /* Post card */
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

  /* Reel viewport */
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

  /* Carousel */
  .carousel-counter {
    text-align: center;
    color: #666;
    font-size: 0.78rem;
    padding: 6px 0;
    background: #212121;
  }

  /* Download button */
  .stDownloadButton > button {
    width: 100% !important;
    background: #ff0000 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    padding: 11px 16px !important;
    min-height: 44px !important;
    -webkit-tap-highlight-color: transparent;
  }
  .stDownloadButton > button:hover { background: #cc0000 !important; }

  /* Primary action button */
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

  /* All buttons base */
  .stButton > button,
  [data-testid^="baseButton"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100% !important;
    min-height: 44px !important;
    font-size: 0.9rem !important;
    -webkit-tap-highlight-color: transparent;
  }

  /* Secondary button */
  .stButton > button[kind="secondary"],
  [data-testid="baseButton-secondary"] {
    background: #272727 !important;
    color: #aaa !important;
    border: 1px solid #303030 !important;
  }

  /* Reduce gap between columns */
  [data-testid="stHorizontalBlock"] { gap: 6px !important; }

  /* Load more wrapper */
  .load-more-wrap { margin: 4px 0 20px; }

  /* Inputs */
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

  .streamlit-expanderHeader {
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    min-height: 44px !important;
  }

  hr { border-color: #272727 !important; margin: 8px 0 14px !important; }
  .stAlert { border-radius: 8px !important; font-size: 0.85rem !important; }

  /* Resolution badge */
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

  /* Section label */
  .section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #555;
    margin: 0 0 10px;
  }

  /* Auth notice */
  .auth-notice {
    background: #1a1000;
    border: 1px solid #3a2800;
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 0.83rem;
    color: #ccaa55;
    margin: 8px 0 12px;
  }

  /* Story timestamp */
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

  /* YouTube card */
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

  /* Progress bar */
  .stProgress > div > div > div {
    background: #ff0000 !important;
  }

  .stApp { background: #0f0f0f !important; }
</style>
""", unsafe_allow_html=True)


# ── Client management ─────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _make_auth_client(session_id: str) -> Client:
    cl = Client()
    cl.delay_range = [2, 4]
    cl.login_by_sessionid(session_id)
    return cl


@st.cache_resource(show_spinner=False)
def _make_anon_client() -> Client:
    cl = Client()
    cl.delay_range = [1, 3]
    return cl


def get_cl() -> tuple:
    """Returns (Client, is_authenticated)."""
    sid = st.session_state.get("session_id", "")
    if sid:
        try:
            return _make_auth_client(sid), True
        except Exception:
            pass
    return _make_anon_client(), False


def handle_session_expiry():
    _make_auth_client.clear()
    for key in list(st.session_state.keys()):
        if key not in ("main_tab", "ig_sub_tab"):
            del st.session_state[key]
    st.error("Your Instagram session has expired. Paste a fresh sessionid in the Session ID panel above.")
    st.rerun()


def full_reset():
    _make_auth_client.clear()
    _make_anon_client.clear()
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


def reset_ig_state():
    """Clear profile/post data but keep session and tab selection."""
    keys = [
        "ig_resolved_username", "ig_uid", "ig_user",
        "ig_feed_data", "ig_reels_data", "ig_stories_data",
        "ig_posts_amount", "ig_reels_amount",
        "ig_posts_has_more", "ig_reels_has_more",
        "ig_post_url", "ig_story_url",
    ]
    for k in keys:
        st.session_state.pop(k, None)
    for k in list(st.session_state.keys()):
        if k.startswith(("full_media_", "carousel_", "dlbytes_")):
            del st.session_state[k]


# ── API call helpers ──────────────────────────────────────────────────────────

def api_call(fn, *args, retries=2, base_wait=8, **kwargs):
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except LoginRequired:
            raise
        except Exception as e:
            msg = str(e).lower()
            is_rate = any(k in msg for k in [
                "wait a few minutes", "429", "rate", "please wait", "too many"
            ])
            if is_rate and attempt < retries - 1:
                wait = base_wait * (attempt + 1)
                placeholder = st.empty()
                for remaining in range(wait, 0, -1):
                    placeholder.warning(
                        f"Instagram rate limit — retrying in {remaining}s "
                        f"(attempt {attempt + 2}/{retries})"
                    )
                    time.sleep(1)
                placeholder.empty()
            else:
                raise


# ── Media helpers ─────────────────────────────────────────────────────────────

def best_image_url(media) -> str:
    try:
        iv2 = getattr(media, "image_versions2", None)
        if iv2 is not None:
            candidates = getattr(iv2, "candidates", None)
            if candidates is None:
                try:
                    candidates = iv2.get("candidates", [])
                except AttributeError:
                    candidates = []
            if candidates:
                if hasattr(candidates[0], "url"):
                    return sorted(candidates, key=lambda x: getattr(x, "width", 0), reverse=True)[0].url
                else:
                    return sorted(candidates, key=lambda x: x.get("width", 0), reverse=True)[0]["url"]
    except Exception:
        pass
    if getattr(media, "thumbnail_url", None):
        return str(media.thumbnail_url)
    return ""


def all_video_versions(media) -> list:
    """Returns [(url, label, filename), ...] sorted by resolution descending."""
    try:
        versions = getattr(media, "video_versions", None) or []
        if not versions:
            url = str(getattr(media, "video_url", "") or "")
            return [(url, "HD", "video_HD.mp4")] if url else []

        def sort_key(v):
            w = v.width if hasattr(v, "width") else v.get("width", 0)
            h = v.height if hasattr(v, "height") else v.get("height", 0)
            return (max(w, h), w * h)

        sorted_v = sorted(versions, key=sort_key, reverse=True)
        seen, result = set(), []
        for v in sorted_v:
            w = v.width if hasattr(v, "width") else v.get("width", 0)
            h = v.height if hasattr(v, "height") else v.get("height", 0)
            url = str(v.url if hasattr(v, "url") else v.get("url", ""))
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


def fetch_bytes(url: str, retries: int = 2) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Referer": "https://www.instagram.com/",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    last_err = None
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=60, headers=headers, stream=False)
            r.raise_for_status()
            return r.content
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(2)
    raise last_err


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


def get_full_media_cached(cl: Client, pk):
    cache_key = f"full_media_{pk}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    try:
        media = api_call(cl.media_info, pk)
        st.session_state[cache_key] = media
        return media
    except Exception:
        return None


def get_cached_bytes(url: str, cache_key: str):
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    try:
        data = fetch_bytes(url)
        st.session_state[cache_key] = data
        return data
    except Exception:
        return None


# ── Input detection ───────────────────────────────────────────────────────────

def detect_input_type(text: str) -> str:
    t = text.strip()
    if "instagram.com" in t:
        if "/stories/" in t:
            return "story_url"
        if "/p/" in t or "/reel/" in t or "/tv/" in t:
            return "post_url"
        return "profile_url"
    if t:
        return "username"
    return "unknown"


def extract_username_from_url(url: str) -> str:
    url = url.rstrip("/")
    parts = url.split("/")
    skip = {"", "www.instagram.com", "instagram.com", "p", "reel", "tv", "stories", "explore"}
    for i, part in enumerate(parts):
        if part in ("www.instagram.com", "instagram.com") and i + 1 < len(parts):
            candidate = parts[i + 1]
            if candidate not in skip:
                return candidate
    return parts[-1] if parts else ""


# ── Carousel renderer ─────────────────────────────────────────────────────────

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
        if img_url:
            st.image(img_url, use_container_width=True)
        else:
            st.caption("Image unavailable.")

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


# ── Download buttons ──────────────────────────────────────────────────────────

def render_download_buttons(media, all_items: list, key: str,
                             is_reel_mode: bool = False, cl: Client = None):
    if not all_items:
        st.caption("No downloadable media found.")
        return

    if is_reel_mode or media.media_type == 2:
        cached_full = st.session_state.get(f"full_media_{media.pk}")
        if cached_full:
            all_items = [
                (f"Download {rl}", url, fn, rl)
                for url, rl, fn in all_video_versions(cached_full)
            ]

        if cl and not cached_full:
            if st.button("Fetch Highest Quality", key=f"fhd_btn_{key}", use_container_width=True):
                with st.spinner("Fetching highest quality..."):
                    full = get_full_media_cached(cl, media.pk)
                    if full:
                        new_v = all_video_versions(full)
                        st.toast("Higher quality available." if new_v else "Already at best quality.")
                    else:
                        st.toast("Could not fetch quality info.")
                st.rerun()

        if not all_items:
            st.caption("No video versions found.")
            return

        best_lbl, best_url, best_fn, best_rl = all_items[0]
        dl_cache_key = f"dlbytes_{media.pk}_best"
        star_label = f"Download  {best_rl} (Best)" if best_rl else "Download Video"
        ctx = st.spinner(f"Preparing {best_rl}...") if dl_cache_key not in st.session_state else contextlib_nullcontext()
        with ctx:
            data = get_cached_bytes(best_url, dl_cache_key)
        if data:
            st.download_button(
                star_label, data=data,
                file_name=f"{media.pk}_{best_fn}",
                mime="video/mp4",
                key=f"dl_{key}_best",
                use_container_width=True,
            )
        else:
            st.caption("Could not load video. URL may have expired.")

        if len(all_items) > 1:
            with st.expander("More quality options"):
                for i, (lbl, url, fname, rlabel) in enumerate(all_items[1:], start=1):
                    res_cache_key = f"dlbytes_{media.pk}_res{i}"
                    data = get_cached_bytes(url, res_cache_key)
                    if data:
                        st.download_button(
                            f"Download {rlabel}", data=data,
                            file_name=f"{media.pk}_{fname}",
                            mime="video/mp4",
                            key=f"dl_{key}_res{i}",
                            use_container_width=True,
                        )
                    else:
                        st.caption(f"{rlabel} unavailable")

    elif len(all_items) == 1:
        lbl, url, fname, rlabel = all_items[0]
        res_info = f" {rlabel}" if rlabel else ""
        dl_cache_key = f"dlbytes_{media.pk}_single"
        data = get_cached_bytes(url, dl_cache_key)
        if data:
            st.download_button(
                f"Download{res_info}", data=data,
                file_name=f"{media.pk}_{fname}",
                mime="video/mp4" if fname.endswith(".mp4") else "image/jpeg",
                key=f"dl_{key}_single",
                use_container_width=True,
            )
        else:
            st.caption("Download unavailable. URL may have expired.")

    else:
        cols = st.columns(2)
        for i, (lbl, url, fname, rlabel) in enumerate(all_items):
            dl_cache_key = f"dlbytes_{media.pk}_album{i}"
            with cols[i % 2]:
                data = get_cached_bytes(url, dl_cache_key)
                if data:
                    st.download_button(
                        f"Download {lbl}", data=data,
                        file_name=f"{media.pk}_{fname}",
                        mime="video/mp4" if fname.endswith(".mp4") else "image/jpeg",
                        key=f"dl_{key}_{i}",
                        use_container_width=True,
                    )
                else:
                    st.caption(f"{lbl} unavailable")
        zip_cache_key = f"dlbytes_{media.pk}_zip"
        if zip_cache_key not in st.session_state:
            try:
                st.session_state[zip_cache_key] = make_zip(all_items)
            except Exception as e:
                st.error(f"ZIP failed: {e}")
        zip_data = st.session_state.get(zip_cache_key)
        if zip_data:
            st.download_button(
                "Download All as ZIP", data=zip_data,
                file_name=f"{media.pk}_all.zip", mime="application/zip",
                key=f"dl_{key}_zip", use_container_width=True,
            )


# ── Post card ─────────────────────────────────────────────────────────────────

def render_post(media, idx: int, show_reel_aspect: bool = False, cl: Client = None):
    key = f"post_{idx}_{media.pk}"
    is_vid = media.media_type == 2
    label, badge_cls = media_type_label(media)
    username = media.user.username if media.user else "unknown"
    caption = media.caption_text or ""

    display_media = st.session_state.get(f"full_media_{media.pk}", media)

    if is_vid:
        all_items = [
            (f"Download {rl}", url, fn, rl)
            for url, rl, fn in all_video_versions(display_media)
        ]
    elif media.media_type == 8:
        all_items = []
        for i, res in enumerate(media.resources):
            if res.media_type == 2:
                for url, rl, fn in all_video_versions(res):
                    all_items.append((f"Video {i + 1} {rl}", url, f"v{i + 1}_{fn}", rl))
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
        vurl, res_label = best_video_url(display_media)
        if not vurl:
            vurl = str(getattr(media, "video_url", "") or "")
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
        if img_url:
            st.image(img_url, use_container_width=True)

    if caption:
        short = caption[:140] + ("..." if len(caption) > 140 else "")
        st.markdown(f'<div class="post-caption">{short}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

    render_download_buttons(
        media, all_items, key,
        is_reel_mode=(show_reel_aspect and is_vid),
        cl=cl,
    )
    st.markdown("---")


# ── Story card ────────────────────────────────────────────────────────────────

def render_story(story, idx: int):
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
        if img_url:
            st.image(img_url, use_container_width=True)
        else:
            st.caption("Image unavailable.")

    taken_at = getattr(story, "taken_at", None)
    ts = taken_at.strftime("%b %d, %Y  %H:%M") if taken_at else ""
    st.markdown(f'<div class="story-meta">{ts}</div>', unsafe_allow_html=True)

    if is_vid:
        versions = all_video_versions(story)
        if versions:
            url, label, fname = versions[0]
            cache_key = f"dlbytes_story_{story.pk}_v"
            data = get_cached_bytes(url, cache_key)
            if data:
                st.download_button(
                    f"Download {label}",
                    data=data,
                    file_name=f"story_{story.pk}_{fname}",
                    mime="video/mp4",
                    key=f"dl_{key}_vid",
                    use_container_width=True,
                )
            else:
                st.caption("Video unavailable. URL may have expired.")
    else:
        img_url = best_image_url(story)
        if img_url:
            cache_key = f"dlbytes_story_{story.pk}_img"
            data = get_cached_bytes(img_url, cache_key)
            if data:
                st.download_button(
                    "Download Photo",
                    data=data,
                    file_name=f"story_{story.pk}.jpg",
                    mime="image/jpeg",
                    key=f"dl_{key}_img",
                    use_container_width=True,
                )

    st.markdown("---")


# ── YouTube helpers ───────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _get_ffmpeg_path() -> str | None:
    """Return path to ffmpeg binary (bundled via imageio-ffmpeg, or system)."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def download_yt_video(url: str) -> tuple:
    """Download best quality YouTube/Shorts video. Returns (bytes, filename, info_dict)."""
    ffmpeg = _get_ffmpeg_path()

    with tempfile.TemporaryDirectory() as tmpdir:
        outtmpl = os.path.join(tmpdir, "video.%(ext)s")

        ydl_opts = {
            # Best video + best audio merged → true highest quality
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }
        if ffmpeg:
            ydl_opts["ffmpeg_location"] = ffmpeg

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True) or {}

        files = [f for f in os.listdir(tmpdir) if not f.endswith(".part")]
        if not files:
            raise Exception("Download failed: no output file was created.")

        filepath = os.path.join(tmpdir, files[0])
        with open(filepath, "rb") as f:
            data = f.read()

        title = info.get("title", "video")
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()[:80]
        ext = os.path.splitext(files[0])[1] or ".mp4"
        return data, f"{safe_title}{ext}", info


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
        if st.button("Reset", key="yt_reset_btn", type="secondary", use_container_width=True):
            st.session_state.pop("yt_data", None)
            st.session_state.pop("yt_filename", None)
            st.session_state.pop("yt_info", None)
            st.session_state["yt_url_input"] = ""
            st.rerun()

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
            "Save Video",
            data=yt_data,
            file_name=st.session_state.get("yt_filename", "video.mp4"),
            mime="video/mp4",
            key="yt_dl_final",
            use_container_width=True,
        )


# ── Instagram auth notice ─────────────────────────────────────────────────────

def render_auth_notice(uname: str = ""):
    who = f"@{uname}" if uname else "This content"
    st.markdown(
        f'<div class="auth-notice">'
        f'<strong>{who}</strong> requires a Session ID to access. '
        f'Open the Session ID panel above and paste your sessionid cookie.'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Instagram single-item renders ─────────────────────────────────────────────

def render_ig_single_post(url: str, cl: Client, is_auth: bool):
    with st.spinner("Fetching media..."):
        try:
            pk = api_call(cl.media_pk_from_url, url)
            media = api_call(cl.media_info, pk)
        except LoginRequired:
            if is_auth:
                handle_session_expiry()
            else:
                render_auth_notice()
            return
        except Exception as e:
            err = str(e)
            if "wait a few minutes" in err.lower() or "please wait" in err.lower():
                st.error("Rate limited. Please wait 2-5 minutes and try again.")
            else:
                st.error(f"Could not fetch media: {err}")
            return
    render_post(media, idx=99999, show_reel_aspect=is_reel(media), cl=cl)


def render_ig_single_story(url: str, cl: Client, is_auth: bool):
    with st.spinner("Fetching story..."):
        try:
            pk = api_call(cl.story_pk_from_url, url)
            story = api_call(cl.story_info, pk)
        except LoginRequired:
            if is_auth:
                handle_session_expiry()
            else:
                render_auth_notice()
                st.info("Stories require a Session ID — Instagram restricts story access to logged-in users.")
            return
        except Exception as e:
            st.error(f"Could not fetch story: {e}")
            return
    render_story(story, idx=0)


# ── Instagram profile sections ────────────────────────────────────────────────

def render_ig_feed(uname: str, uid, cl: Client, is_auth: bool):
    amt = st.session_state.get("ig_posts_amount", PAGE_SIZE)

    if st.session_state.get("ig_feed_data") is None:
        with st.spinner(f"Loading @{uname}'s posts..."):
            try:
                raw = api_call(cl.user_medias, uid, amount=amt)
                posts = [m for m in raw if not is_reel(m)]
                st.session_state["ig_feed_data"] = posts
                st.session_state["ig_posts_has_more"] = len(raw) >= amt
            except LoginRequired:
                if is_auth:
                    handle_session_expiry()
                else:
                    render_auth_notice(uname)
                return
            except Exception as e:
                st.error(f"Could not load posts: {e}")
                return

    posts = st.session_state.get("ig_feed_data") or []
    if not posts:
        st.info("No posts found for this account.")
        return

    st.markdown(f'<p class="section-label">{len(posts)} posts loaded</p>', unsafe_allow_html=True)
    for i, media in enumerate(posts):
        try:
            render_post(media, i, show_reel_aspect=False, cl=cl)
        except Exception as e:
            st.warning(f"Could not render post {i + 1}: {e}")

    if st.session_state.get("ig_posts_has_more", False):
        st.markdown('<div class="load-more-wrap">', unsafe_allow_html=True)
        if st.button(f"Load {PAGE_SIZE} More Posts", use_container_width=True, key="load_more_posts"):
            st.session_state["ig_posts_amount"] = amt + PAGE_SIZE
            st.session_state["ig_feed_data"] = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("All available posts loaded.")


def render_ig_reels(uname: str, uid, cl: Client, is_auth: bool):
    amt = st.session_state.get("ig_reels_amount", PAGE_SIZE)

    if st.session_state.get("ig_reels_data") is None:
        with st.spinner(f"Loading @{uname}'s reels..."):
            try:
                try:
                    reels = api_call(cl.user_clips, uid, amount=amt)
                except Exception:
                    raw = api_call(cl.user_medias, uid, amount=amt)
                    reels = [m for m in raw if is_reel(m)]

                seen, uniq = set(), []
                for r in reels:
                    if r.pk not in seen:
                        uniq.append(r)
                        seen.add(r.pk)

                st.session_state["ig_reels_data"] = uniq
                st.session_state["ig_reels_has_more"] = len(uniq) >= amt
            except LoginRequired:
                if is_auth:
                    handle_session_expiry()
                else:
                    render_auth_notice(uname)
                return
            except Exception as e:
                st.error(f"Could not load reels: {e}")
                return

    reels = st.session_state.get("ig_reels_data") or []
    if not reels:
        st.info("No reels found. This account may have no public reels.")
        return

    st.markdown(f'<p class="section-label">{len(reels)} reels loaded</p>', unsafe_allow_html=True)
    for i, media in enumerate(reels):
        try:
            render_post(media, i + 10000, show_reel_aspect=True, cl=cl)
        except Exception as e:
            st.warning(f"Could not render reel {i + 1}: {e}")

    if st.session_state.get("ig_reels_has_more", False):
        st.markdown('<div class="load-more-wrap">', unsafe_allow_html=True)
        if st.button(f"Load {PAGE_SIZE} More Reels", use_container_width=True, key="load_more_reels"):
            st.session_state["ig_reels_amount"] = amt + PAGE_SIZE
            st.session_state["ig_reels_data"] = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("All available reels loaded.")


def render_ig_stories(uname: str, uid, cl: Client, is_auth: bool):
    if st.session_state.get("ig_stories_data") is None:
        with st.spinner(f"Loading @{uname}'s stories..."):
            try:
                stories = api_call(cl.user_stories, uid)
                st.session_state["ig_stories_data"] = stories or []
            except LoginRequired:
                if is_auth:
                    handle_session_expiry()
                else:
                    render_auth_notice(uname)
                    st.info("Stories require a Session ID — Instagram limits story access to logged-in users.")
                return
            except Exception as e:
                st.error(f"Could not load stories: {e}")
                return

    stories = st.session_state.get("ig_stories_data") or []
    if not stories:
        st.info("No active stories. Stories expire after 24 hours.")
        return

    st.markdown(f'<p class="section-label">{len(stories)} active stories</p>', unsafe_allow_html=True)
    for i, story in enumerate(stories):
        try:
            render_story(story, i)
        except Exception as e:
            st.warning(f"Could not render story {i + 1}: {e}")


# ── Instagram tab ─────────────────────────────────────────────────────────────

def render_instagram_tab():
    cl, is_auth = get_cl()

    # Session ID panel
    with st.expander(
        "Session ID",
        expanded=False,
    ):
        session_input = st.text_input(
            "Instagram Session ID",
            type="password",
            placeholder="Paste sessionid cookie here",
            help="Browser > instagram.com > DevTools (F12) > Application > Cookies > sessionid",
            key="session_id_input",
        )
        cs1, cs2 = st.columns(2)
        with cs1:
            if st.button("Save Session", key="save_session"):
                if session_input.strip():
                    _make_auth_client.clear()
                    st.session_state["session_id"] = session_input.strip()
                    st.success("Session saved.")
                    st.rerun()
                else:
                    st.error("Session ID cannot be empty.")
        with cs2:
            if st.button("Clear Session", key="clear_session", type="secondary"):
                st.session_state.pop("session_id", None)
                _make_auth_client.clear()
                st.rerun()

        if "session_id" not in st.session_state:
            st.markdown("""
**How to get Session ID:**
1. Open Instagram in a desktop browser and log in
2. Press **F12** — Application — Cookies — `instagram.com`
3. Copy the value of **`sessionid`**
            """)
            st.caption("Without a Session ID you can still access public posts and reels.")

    st.markdown("---")

    # Sub-tab navigation: Feed | Reels | Stories
    ig_sub = st.session_state.get("ig_sub_tab", "feed")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Feed", key="sub_feed",
                     type="primary" if ig_sub == "feed" else "secondary",
                     use_container_width=True):
            st.session_state["ig_sub_tab"] = "feed"
            st.rerun()
    with c2:
        if st.button("Reels", key="sub_reels",
                     type="primary" if ig_sub == "reels" else "secondary",
                     use_container_width=True):
            st.session_state["ig_sub_tab"] = "reels"
            st.rerun()
    with c3:
        if st.button("Stories", key="sub_stories",
                     type="primary" if ig_sub == "stories" else "secondary",
                     use_container_width=True):
            st.session_state["ig_sub_tab"] = "stories"
            st.rerun()

    placeholder_map = {
        "feed": "Username, profile URL, or post URL",
        "reels": "Username, profile URL, or reel URL",
        "stories": "Username, profile URL, or story URL",
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
        if st.button("Reset", type="secondary", key="ig_reset_btn", use_container_width=True):
            reset_ig_state()
            st.session_state["ig_raw_input"] = ""
            st.rerun()

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
            uname = extract_username_from_url(text) if input_type == "profile_url" else text
            if uname:
                st.session_state["ig_resolved_username"] = uname
                st.session_state["ig_posts_amount"] = PAGE_SIZE
                st.session_state["ig_reels_amount"] = PAGE_SIZE
        st.rerun()

    # Single post/reel URL
    post_url = st.session_state.get("ig_post_url")
    if post_url:
        render_ig_single_post(post_url, cl, is_auth)
        return

    # Single story URL
    story_url = st.session_state.get("ig_story_url")
    if story_url:
        render_ig_single_story(story_url, cl, is_auth)
        return

    # Profile browsing
    uname = st.session_state.get("ig_resolved_username")
    if not uname:
        return

    # Resolve user info once
    if not st.session_state.get("ig_uid"):
        with st.spinner(f"Looking up @{uname}..."):
            try:
                user = api_call(cl.user_info_by_username, uname)
                st.session_state["ig_user"] = user
                st.session_state["ig_uid"] = user.pk
            except LoginRequired:
                if is_auth:
                    handle_session_expiry()
                else:
                    render_auth_notice(uname)
                return
            except Exception as e:
                st.error(f"Could not look up @{uname}: {e}")
                return

    uid = st.session_state["ig_uid"]
    user = st.session_state.get("ig_user")

    # Profile header
    if user:
        c1, c2 = st.columns([1, 4])
        with c1:
            pic = str(user.profile_pic_url) if user.profile_pic_url else ""
            if pic:
                st.image(pic, width=64)
        with c2:
            st.markdown(f"**@{user.username}**")
            st.caption(f"{user.media_count:,} posts  ·  {user.follower_count:,} followers")
        st.markdown("---")

    if ig_sub == "feed":
        render_ig_feed(uname, uid, cl, is_auth)
    elif ig_sub == "reels":
        render_ig_reels(uname, uid, cl, is_auth)
    elif ig_sub == "stories":
        render_ig_stories(uname, uid, cl, is_auth)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(
    '<div class="topbar"><h1>SapZap</h1></div>',
    unsafe_allow_html=True,
)

# Main tab selector: Instagram | YouTube
main_tab = st.session_state.get("main_tab", "youtube")
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
