import streamlit as st
import requests
import zipfile
import io
import time
import contextlib
from contextlib import nullcontext as contextlib_nullcontext
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

PAGE_SIZE = 24

st.set_page_config(
    page_title="SapZap",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
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

  /* ── Top bar ── */
  .topbar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 0 16px;
    border-bottom: 1.5px solid #262626;
    margin-bottom: 16px;
  }
  .topbar h1 {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #f58529, #dd2a7b, #8134af, #515bd4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  /* ── Post card ── */
  .post-card {
    border: 1px solid #262626;
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 18px;
    background: #0a0a0a;
  }
  .post-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    min-width: 0;
    overflow: hidden;
  }
  .post-username {
    font-size: 0.85rem;
    font-weight: 600;
    color: #fff;
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .post-badge {
    flex-shrink: 0;
    margin-left: 8px;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    border-radius: 20px;
    padding: 3px 9px;
  }
  .badge-photo  { background: #1a3a5c; color: #58a6ff; }
  .badge-video  { background: #1a2e1a; color: #56d364; }
  .badge-reel   { background: #3a1a3a; color: #f0a0f0; }
  .badge-album  { background: #3a2a0a; color: #e3b341; }

  .post-caption {
    padding: 8px 12px 12px;
    font-size: 0.8rem;
    color: #ccc;
    line-height: 1.5;
    border-top: 1px solid #1a1a1a;
    word-break: break-word;
    overflow-wrap: break-word;
  }

  /* ── Media areas ── */
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

  /* ── Carousel ── */
  .carousel-counter {
    text-align: center;
    color: #888;
    font-size: 0.78rem;
    padding: 6px 0;
    background: #0a0a0a;
  }

  /* ── Download buttons ── */
  .stDownloadButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #f58529, #dd2a7b) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    padding: 11px 16px !important;
    min-height: 44px !important;
    -webkit-tap-highlight-color: transparent;
  }
  .stDownloadButton > button:hover { opacity: 0.9 !important; }

  /* ── Action buttons ── */
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #f58529, #dd2a7b) !important;
    color: #fff !important;
    border: none !important;
    min-height: 44px !important;
  }
  .stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100% !important;
    min-height: 44px !important;
    font-size: 0.9rem !important;
    -webkit-tap-highlight-color: transparent;
  }

  /* ── Reset / danger button ── */
  .stButton > button[kind="secondary"] {
    background: #1a1a1a !important;
    color: #aaa !important;
    border: 1px solid #333 !important;
  }

  /* ── Load more button ── */
  .load-more-wrap { margin: 4px 0 20px; }

  /* ── Inputs ── */
  .stTextInput input {
    border-radius: 10px !important;
    font-size: 1rem !important;
    min-height: 44px !important;
    padding: 10px 14px !important;
    background: #111 !important;
    color: #fff !important;
    border: 1px solid #333 !important;
  }
  .stTextInput input:focus {
    border-color: #dd2a7b !important;
    box-shadow: 0 0 0 2px rgba(221,42,123,0.2) !important;
  }

  /* ── Radio ── */
  .stRadio > div { gap: 8px !important; }
  .stRadio label { font-size: 0.85rem !important; }

  .streamlit-expanderHeader {
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    min-height: 44px !important;
  }

  hr { border-color: #1a1a1a !important; margin: 8px 0 16px !important; }
  .stAlert { border-radius: 10px !important; font-size: 0.85rem !important; }

  /* ── Resolution badge ── */
  .res-badge {
    display: inline-block;
    font-size: 0.65rem; font-weight: 700;
    background: #1c2a1c; color: #56d364;
    border-radius: 4px; padding: 1px 5px;
    margin-left: 4px; vertical-align: middle;
  }

  /* ── Section label ── */
  .section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #666;
    margin: 0 0 10px;
  }

  /* ── Session-required notice ── */
  .auth-notice {
    background: #1a1200;
    border: 1px solid #4a3300;
    border-radius: 10px;
    padding: 12px 14px;
    font-size: 0.83rem;
    color: #f0c060;
    margin: 8px 0 12px;
  }

  .stApp { background: #000 !important; }
</style>
""", unsafe_allow_html=True)


# ── Client management ─────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _make_auth_client(session_id: str) -> Client:
    """Authenticated client cached by session_id string."""
    cl = Client()
    cl.delay_range = [2, 4]
    cl.login_by_sessionid(session_id)
    return cl


@st.cache_resource(show_spinner=False)
def _make_anon_client() -> Client:
    """Unauthenticated client for attempting public content."""
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
    """Session expired mid-use — clear everything and prompt re-login."""
    _make_auth_client.clear()
    for key in list(st.session_state.keys()):
        if key != "main_tab":
            del st.session_state[key]
    st.error(
        "🔑 **Your Instagram session has expired.**  "
        "Please open the Session ID panel above and paste a fresh sessionid."
    )
    st.rerun()


def full_reset():
    """Wipe all state and cached clients."""
    _make_auth_client.clear()
    _make_anon_client.clear()
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


def reset_feed_state():
    """Clear only the feed/profile data, keep session ID."""
    feed_keys = [
        "feed_username", "feed_uid", "feed_user",
        "feed_data", "reels_data",
        "feed_content_type", "posts_amount", "reels_amount",
        "posts_has_more", "reels_has_more", "sub_tab",
    ]
    for k in feed_keys:
        st.session_state.pop(k, None)
    # Clear per-media caches
    for k in list(st.session_state.keys()):
        if k.startswith("full_media_") or k.startswith("carousel_"):
            del st.session_state[k]


# ── API call helpers ──────────────────────────────────────────────────────────

def api_call(fn, *args, retries=2, base_wait=8, **kwargs):
    """Retry with back-off on rate-limit errors; propagate LoginRequired."""
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
                wait = base_wait * (attempt + 1)   # 8s, 16s — not exponential blowup
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
            # instagrapi returns an ImageVersions2 Pydantic model; access .candidates directly
            candidates = getattr(iv2, "candidates", None)
            if candidates is None:
                # fallback: try dict-style access for raw dicts
                try:
                    candidates = iv2.get("candidates", [])
                except AttributeError:
                    candidates = []
            if candidates:
                return sorted(candidates, key=lambda x: getattr(x, "width", 0) if hasattr(x, "width") else x.get("width", 0), reverse=True)[0].url if hasattr(candidates[0], "url") else \
                       sorted(candidates, key=lambda x: x.get("width", 0), reverse=True)[0]["url"]
    except Exception:
        pass
    if getattr(media, "thumbnail_url", None):
        return str(media.thumbnail_url)
    return ""


def all_video_versions(media) -> list:
    """
    Returns [(url, label, filename), ...] sorted by resolution descending.
    Handles both landscape and vertical (reel) orientations.
    """
    try:
        versions = getattr(media, "video_versions", None) or []
        if not versions:
            url = str(getattr(media, "video_url", "") or "")
            return [(url, "HD", "video_HD.mp4")] if url else []

        def sort_key(v):
            w = v.width if hasattr(v, "width") else v.get("width", 0)
            h = v.height if hasattr(v, "height") else v.get("height", 0)
            # Use the longer dimension as primary sort (handles portrait reels)
            long_side = max(w, h)
            pixels = w * h
            return (long_side, pixels)

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
    t  = media.media_type
    pt = (getattr(media, "product_type", "") or "").lower()
    if t == 1: return "Photo", "badge-photo"
    if t == 2:
        if "reel" in pt or "clips" in pt:
            return "Reel", "badge-reel"
        return "Video", "badge-video"
    if t == 8: return f"Album · {len(media.resources)}", "badge-album"
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
    """
    Fetch full media_info for a given pk and cache it in session_state.
    Returns the media object, or None on failure.
    """
    cache_key = f"full_media_{pk}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    try:
        media = api_call(cl.media_info, pk)
        st.session_state[cache_key] = media
        return media
    except Exception:
        return None


# ── Carousel renderer ─────────────────────────────────────────────────────────

def render_carousel(media, key: str):
    resources = media.resources
    n         = len(resources)
    if n == 0:
        st.caption("No items in album.")
        return
    sk        = f"carousel_{key}"
    if sk not in st.session_state:
        st.session_state[sk] = 0
    idx = min(st.session_state[sk], n - 1)   # guard against stale index
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
            st.session_state[sk] = max(0, idx - 1); st.rerun()
    with c2:
        if st.button("Next", key=f"next_{key}", disabled=(idx == n - 1), use_container_width=True):
            st.session_state[sk] = min(n - 1, idx + 1); st.rerun()


# ── Download buttons ──────────────────────────────────────────────────────────

def get_cached_bytes(url: str, cache_key: str) -> bytes | None:
    """Fetch bytes and cache in session_state. Returns None on failure."""
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    try:
        data = fetch_bytes(url)
        st.session_state[cache_key] = data
        return data
    except Exception:
        return None


def render_download_buttons(media, all_items: list, key: str,
                             is_reel_mode: bool = False, cl: Client = None):
    if not all_items:
        st.caption("No downloadable media found.")
        return

    if is_reel_mode or media.media_type == 2:
        # Use cached full-quality version if available
        cached_full = st.session_state.get(f"full_media_{media.pk}")
        if cached_full:
            all_items = [
                (f"Download {rl}", url, fn, rl)
                for url, rl, fn in all_video_versions(cached_full)
            ]

        # Offer "Fetch Full Quality" when no full media cached yet
        if cl and not cached_full:
            if st.button(
                "Fetch Highest Quality",
                key=f"fhd_btn_{key}",
                use_container_width=True,
            ):
                with st.spinner("Fetching highest quality available..."):
                    full = get_full_media_cached(cl, media.pk)
                    if full:
                        new_versions = all_video_versions(full)
                        if new_versions:
                            st.toast("Higher quality available!")
                        else:
                            st.toast("Already at best available quality.")
                    else:
                        st.toast("Could not fetch quality info.")
                st.rerun()

        # Best quality button
        best_lbl, best_url, best_fn, best_rl = all_items[0]
        dl_cache_key = f"dlbytes_{media.pk}_best"
        star_label = f"Download  {best_rl} (Best)" if best_rl else "Download Video"
        with st.spinner(f"Preparing {best_rl}...") if dl_cache_key not in st.session_state else contextlib_nullcontext():
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
            st.caption(f"Could not load {best_rl} — URL may have expired. Re-fetch the post.")

        # Other resolutions in expander
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
            st.caption("Download unavailable — URL may have expired. Re-fetch the post.")

    else:
        # Album — 2-column grid + ZIP
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
        # ZIP button
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


# ── Post / Reel card renderer ─────────────────────────────────────────────────

def render_post(media, idx: int, show_reel_aspect: bool = False, cl: Client = None):
    key      = f"post_{idx}_{media.pk}"
    is_vid   = media.media_type == 2
    label, badge_cls = media_type_label(media)
    username = media.user.username if media.user else "unknown"
    caption  = media.caption_text or ""

    # Use cached full-quality version for video if available
    display_media = st.session_state.get(f"full_media_{media.pk}", media)

    # Build download item list
    if is_vid:
        all_items = [
            (f"⬇ {rl}", url, fn, rl)
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

    # Card header
    st.markdown(f"""
    <div class="post-header" style="border:1px solid #262626;border-radius:14px 14px 0 0;background:#0a0a0a;margin-bottom:0;">
      <span class="post-username">@{username}</span>
      <span class="post-badge {badge_cls}">{label}</span>
    </div>
    """, unsafe_allow_html=True)

    # Media preview
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
                    f'<span class="res-badge">⚡ {res_label}</span></div>',
                    unsafe_allow_html=True
                )
    else:
        img_url = best_image_url(media)
        if img_url:
            st.image(img_url, use_container_width=True)

    # Caption
    if caption:
        short = caption[:140] + ("…" if len(caption) > 140 else "")
        st.markdown(f'<div class="post-caption">{short}</div>', unsafe_allow_html=True)

    # Downloads
    render_download_buttons(
        media, all_items, key,
        is_reel_mode=(show_reel_aspect and is_vid),
        cl=cl,
    )
    st.markdown("---")


# ── URL downloader ────────────────────────────────────────────────────────────

def render_url_downloader():
    st.markdown("### 🔗 Download by URL")
    st.caption("Paste any Instagram post, reel, or video link. No session ID needed for public content.")

    url_input = st.text_input(
        "Instagram URL",
        placeholder="https://www.instagram.com/reel/ABC123/",
        label_visibility="collapsed",
        key="url_dl_input",
    )
    fetch_url_btn = st.button("⚡ Fetch & Download", type="primary", key="url_dl_btn")

    if fetch_url_btn and url_input.strip():
        raw_url = url_input.strip()
        cl, is_auth = get_cl()
        with st.spinner("Fetching media info…"):
            try:
                pk    = api_call(cl.media_pk_from_url, raw_url)
                media = api_call(cl.media_info, pk)
            except LoginRequired:
                if is_auth:
                    # Authenticated client expired
                    handle_session_expiry()
                else:
                    # Needs auth but none provided
                    st.markdown(
                        '<div class="auth-notice">'
                        '🔒 This content requires a <strong>Session ID</strong> to download. '
                        'Open the <em>Session ID</em> panel at the top and paste your sessionid.'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                return
            except Exception as e:
                err = str(e)
                if "wait a few minutes" in err.lower() or "please wait" in err.lower():
                    st.error("⏳ Instagram rate limit reached. Please wait 2–5 minutes and try again.")
                else:
                    st.error(f"Could not fetch URL: {err}")
                return

        st.success("Media found!")
        render_post(media, idx=99999, show_reel_aspect=is_reel(media), cl=cl)


# ── Profile browser ───────────────────────────────────────────────────────────

def render_profile_browser():
    # ── Input row ──────────────────────────────────────────────
    col_u, col_b = st.columns([3, 1])
    with col_u:
        username = st.text_input(
            "Username",
            placeholder="e.g. natgeo",
            label_visibility="collapsed",
            key="username_input",
        )
    with col_b:
        fetch_btn = st.button("Fetch", type="primary", key="fetch_profile_btn")

    # ── Content type BEFORE fetching ───────────────────────────
    content_type = st.radio(
        "What to fetch",
        ["📷 Posts", "🎬 Reels", "📱 Both"],
        horizontal=True,
        index=2,
        key="content_type_radio",
        label_visibility="collapsed",
    )

    if fetch_btn and username.strip():
        uname = username.strip().lstrip("@")
        reset_feed_state()
        st.session_state["feed_username"]    = uname
        st.session_state["feed_content_type"] = content_type
        st.session_state["posts_amount"]     = PAGE_SIZE
        st.session_state["reels_amount"]     = PAGE_SIZE
        st.rerun()

    if not st.session_state.get("feed_username"):
        return

    uname   = st.session_state["feed_username"]
    ct      = st.session_state.get("feed_content_type", "📱 Both")
    need_posts = "Posts" in ct or "Both" in ct
    need_reels = "Reels" in ct or "Both" in ct
    cl, is_auth = get_cl()

    # ── Fetch user info ─────────────────────────────────────────
    if not st.session_state.get("feed_uid"):
        with st.spinner(f"Looking up @{uname}…"):
            try:
                user = api_call(cl.user_info_by_username, uname)
                st.session_state["feed_user"] = user
                st.session_state["feed_uid"]  = user.pk
            except LoginRequired:
                if is_auth:
                    handle_session_expiry()
                else:
                    st.markdown(
                        f'<div class="auth-notice">'
                        f'🔒 <strong>@{uname}</strong> requires a <strong>Session ID</strong> to browse. '
                        f'Add your sessionid in the panel above.'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                return
            except Exception as e:
                st.error(f"Could not look up @{uname}: {e}")
                return

    uid  = st.session_state["feed_uid"]
    user = st.session_state.get("feed_user")

    # ── Fetch posts if needed ───────────────────────────────────
    if need_posts and st.session_state.get("feed_data") is None:
        amt = st.session_state.get("posts_amount", PAGE_SIZE)
        with st.spinner(f"Loading @{uname}'s posts…"):
            try:
                raw   = api_call(cl.user_medias, uid, amount=amt)
                posts = [m for m in raw if not is_reel(m)]
                st.session_state["feed_data"]      = posts
                # Show "Load More" if we received the full requested amount
                st.session_state["posts_has_more"] = len(raw) >= amt
            except LoginRequired:
                if is_auth: handle_session_expiry()
                else:
                    st.markdown(
                        f'<div class="auth-notice">'
                        f'🔒 <strong>@{uname}</strong> requires a <strong>Session ID</strong> to browse.'
                        f'</div>', unsafe_allow_html=True)
                return
            except Exception as e:
                st.error(f"Could not load posts: {e}"); return

    # ── Fetch reels if needed ───────────────────────────────────
    if need_reels and st.session_state.get("reels_data") is None:
        amt = st.session_state.get("reels_amount", PAGE_SIZE)
        with st.spinner(f"Loading @{uname}'s reels…"):
            try:
                try:
                    reels = api_call(cl.user_clips, uid, amount=amt)
                except Exception:
                    # Fallback: pull reels from the general feed
                    raw   = api_call(cl.user_medias, uid, amount=amt)
                    reels = [m for m in raw if is_reel(m)]
                    st.toast(f"ℹ️ Reel endpoint limited — showing {len(reels)} reels from feed.")

                # Deduplicate by pk
                seen, uniq = set(), []
                for r in reels:
                    if r.pk not in seen:
                        uniq.append(r); seen.add(r.pk)

                st.session_state["reels_data"]     = uniq
                st.session_state["reels_has_more"] = len(uniq) >= amt
            except LoginRequired:
                if is_auth: handle_session_expiry()
                else:
                    st.markdown(
                        f'<div class="auth-notice">'
                        f'🔒 <strong>@{uname}</strong> requires a <strong>Session ID</strong> to browse.'
                        f'</div>', unsafe_allow_html=True)
                return
            except Exception as e:
                st.error(f"Could not load reels: {e}"); return

    # ── Profile header ──────────────────────────────────────────
    posts = st.session_state.get("feed_data") or []
    reels = st.session_state.get("reels_data") or []

    if user:
        c1, c2 = st.columns([1, 4])
        with c1:
            pic = str(user.profile_pic_url) if user.profile_pic_url else ""
            if pic: st.image(pic, width=64)
        with c2:
            st.markdown(f"**@{user.username}**")
            st.caption(f"{user.media_count:,} posts · {user.follower_count:,} followers")
        st.markdown("---")

    # ── Sub tabs (only shown when Both was selected) ────────────
    if need_posts and need_reels:
        sub_tab = st.session_state.get("sub_tab", "posts")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"📷 Posts ({len(posts)})", use_container_width=True,
                         type="primary" if sub_tab == "posts" else "secondary",
                         key="sub_tab_posts"):
                st.session_state["sub_tab"] = "posts"; st.rerun()
        with c2:
            if st.button(f"🎬 Reels ({len(reels)})", use_container_width=True,
                         type="primary" if sub_tab == "reels" else "secondary",
                         key="sub_tab_reels"):
                st.session_state["sub_tab"] = "reels"; st.rerun()
        st.markdown("---")
    else:
        sub_tab = "posts" if need_posts else "reels"

    # ── Render posts ────────────────────────────────────────────
    if sub_tab == "posts":
        if not posts:
            st.info("No posts found for this account.")
        else:
            amt_loaded = st.session_state.get("posts_amount", PAGE_SIZE)
            st.markdown(
                f'<p class="section-label">📷 {len(posts)} posts loaded</p>',
                unsafe_allow_html=True,
            )
            for i, media in enumerate(posts):
                try:
                    render_post(media, i, show_reel_aspect=False, cl=cl)
                except Exception as e:
                    st.warning(f"Could not render post {i + 1}: {e}")

            if st.session_state.get("posts_has_more", False):
                st.markdown('<div class="load-more-wrap">', unsafe_allow_html=True)
                if st.button("⬇ Load 24 More Posts", use_container_width=True, key="load_more_posts"):
                    st.session_state["posts_amount"] = amt_loaded + PAGE_SIZE
                    st.session_state["feed_data"]    = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.caption("✅ All available posts loaded.")

    # ── Render reels ────────────────────────────────────────────
    else:
        if not reels:
            st.info("No reels found. This account may have no public reels, or try refreshing.")
        else:
            amt_loaded = st.session_state.get("reels_amount", PAGE_SIZE)
            st.markdown(
                f'<p class="section-label">🎬 {len(reels)} reels loaded</p>',
                unsafe_allow_html=True,
            )
            for i, media in enumerate(reels):
                try:
                    render_post(media, i + 10000, show_reel_aspect=True, cl=cl)
                except Exception as e:
                    st.warning(f"Could not render reel {i + 1}: {e}")

            if st.session_state.get("reels_has_more", False):
                st.markdown('<div class="load-more-wrap">', unsafe_allow_html=True)
                if st.button("⬇ Load 24 More Reels", use_container_width=True, key="load_more_reels"):
                    st.session_state["reels_amount"] = amt_loaded + PAGE_SIZE
                    st.session_state["reels_data"]   = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.caption("✅ All available reels loaded.")


# ═════════════════════════════════════════════════════════════
# MAIN UI
# ═════════════════════════════════════════════════════════════

st.markdown("""
<div class="topbar">
  <span style="font-size:1.8rem">⚡</span>
  <h1>SapZap</h1>
</div>
""", unsafe_allow_html=True)

# ── Session ID panel ──────────────────────────────────────────────────────────
# Expanded only when no session is stored. The app continues without one.
with st.expander(
    "🔑 Session ID  ·  optional for public content",
    expanded="session_id" not in st.session_state,
):
    session_input = st.text_input(
        "Instagram Session ID",
        type="password",
        placeholder="Paste sessionid cookie here",
        help=(
            "Browser → instagram.com → DevTools (F12) "
            "→ Application → Cookies → sessionid"
        ),
        key="session_id_input",
    )
    col_save, col_reset = st.columns(2)
    with col_save:
        if st.button("💾 Save Session", key="save_session"):
            if session_input.strip():
                _make_auth_client.clear()          # evict stale client
                st.session_state["session_id"] = session_input.strip()
                st.success("Session saved ✓")
                st.rerun()
            else:
                st.error("Session ID cannot be empty.")
    with col_reset:
        if st.button("🔄 Reset App", key="reset_app", type="secondary"):
            full_reset()

    if "session_id" not in st.session_state:
        st.markdown("""
**How to get Session ID:**
1. Open Instagram in a desktop browser and log in
2. Press **F12** → Application → Cookies → `instagram.com`
3. Copy the value of **`sessionid`**
        """)
        st.caption("💡 Without a Session ID you can still try public posts and reels.")

# ── Tab selector ──────────────────────────────────────────────────────────────
main_tab = st.session_state.get("main_tab", "url")
col_m1, col_m2 = st.columns(2)
with col_m1:
    if st.button(
        "🔗 Download by URL",
        use_container_width=True,
        type="primary" if main_tab == "url" else "secondary",
        key="main_tab_url",
    ):
        st.session_state["main_tab"] = "url"
        st.rerun()
with col_m2:
    if st.button(
        "👤 Browse Profile",
        use_container_width=True,
        type="primary" if main_tab == "profile" else "secondary",
        key="main_tab_profile",
    ):
        st.session_state["main_tab"] = "profile"
        st.rerun()

st.markdown("---")

# ── Route to active tab ───────────────────────────────────────────────────────
if main_tab == "url":
    render_url_downloader()
else:
    render_profile_browser()





    