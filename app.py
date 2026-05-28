import streamlit as st
import requests
import zipfile
import io
import os
import time
from pathlib import Path
from instagrapi import Client
from instagrapi.types import Media

st.set_page_config(
    page_title="SapZap",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Global */
  html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
  .block-container { padding: 1rem 1rem 2rem; max-width: 480px; margin: auto; }

  /* Hide streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }

  /* Top bar */
  .topbar {
    display: flex; align-items: center; gap: 10px;
    padding: 12px 0 18px;
    border-bottom: 1px solid #dbdbdb;
    margin-bottom: 18px;
  }
  .topbar h1 { font-size: 1.4rem; font-weight: 700; margin: 0; }

  /* Post card */
  .post-card {
    border: 1px solid #dbdbdb;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 20px;
    background: #fff;
  }
  .post-header {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px;
  }
  .post-type-badge {
    font-size: 0.7rem; font-weight: 600;
    background: #f0f0f0; border-radius: 20px;
    padding: 2px 8px; color: #555;
    margin-left: auto;
  }
  .post-caption {
    padding: 8px 14px 12px;
    font-size: 0.83rem; color: #333;
    line-height: 1.45;
    border-top: 1px solid #f0f0f0;
  }

  /* Carousel */
  .carousel-wrap {
    position: relative;
    background: #000;
    aspect-ratio: 1;
    overflow: hidden;
  }
  .carousel-img {
    width: 100%; height: 100%;
    object-fit: contain;
  }
  .carousel-dots {
    display: flex; justify-content: center; gap: 5px;
    padding: 8px 0;
    background: #fafafa;
  }
  .dot { width: 6px; height: 6px; border-radius: 50%; background: #ccc; }
  .dot.active { background: #0095f6; }

  /* Download button styling */
  .stDownloadButton > button {
    width: 100%;
    background: #0095f6 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 8px !important;
  }
  .stDownloadButton > button:hover {
    background: #1877f2 !important;
  }
  div[data-testid="stHorizontalBlock"] .stDownloadButton > button {
    border-radius: 6px !important;
    font-size: 0.78rem !important;
  }

  /* Inputs */
  .stTextInput input {
    border-radius: 8px !important;
    font-size: 0.9rem !important;
  }
  .stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100%;
  }

  /* Video */
  video { width: 100%; aspect-ratio: 1; object-fit: contain; background: #000; }

  /* Spinner */
  .loading-text { text-align: center; color: #888; font-size: 0.9rem; padding: 20px 0; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_client(session_id: str) -> Client:
    cl = Client()
    cl.delay_range = [1, 2]
    cl.login_by_sessionid(session_id)
    return cl


def best_image_url(media: Media) -> str:
    """Return highest resolution image URL."""
    try:
        versions = media.image_versions2.get("candidates", [])
        if versions:
            # Sort by width descending → highest res first
            best = sorted(versions, key=lambda x: x.get("width", 0), reverse=True)[0]
            return best["url"]
    except Exception:
        pass
    if media.thumbnail_url:
        return str(media.thumbnail_url)
    return ""


def fetch_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=30, headers={
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.instagram.com/"
    })
    r.raise_for_status()
    return r.content


def media_type_label(media: Media) -> str:
    t = media.media_type
    pt = getattr(media, "product_type", "") or ""
    if t == 1:
        return "Photo"
    if t == 2:
        return "Reel" if "reel" in pt.lower() else "Video"
    if t == 8:
        return f"Album ({len(media.resources)})"
    return "Post"


def get_all_urls(media: Media):
    """Return list of (label, url, filename) for all items in a post."""
    items = []
    ext_map = {1: "jpg", 2: "mp4", 8: "jpg"}

    if media.media_type == 8:  # Album / carousel
        for i, res in enumerate(media.resources):
            if res.media_type == 2 and res.video_url:
                items.append((f"Video {i+1}", str(res.video_url), f"video_{i+1}.mp4"))
            else:
                img_url = best_image_url(res)
                if img_url:
                    items.append((f"Photo {i+1}", img_url, f"photo_{i+1}.jpg"))
    elif media.media_type == 2 and media.video_url:
        items.append(("Video", str(media.video_url), "video.mp4"))
    else:
        img_url = best_image_url(media)
        if img_url:
            items.append(("Photo", img_url, "photo.jpg"))

    return items


def make_zip(items: list) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for label, url, filename in items:
            try:
                data = fetch_bytes(url)
                zf.writestr(filename, data)
            except Exception:
                pass
    buf.seek(0)
    return buf.read()


# ── Post renderer ─────────────────────────────────────────────────────────────

def render_post(media: Media, idx: int):
    key = f"post_{idx}_{media.pk}"
    all_items = get_all_urls(media)
    caption = media.caption_text or ""
    label = media_type_label(media)

    st.markdown(f"""
    <div class="post-card">
      <div class="post-header">
        <span style="font-size:0.85rem;font-weight:600">@{media.user.username}</span>
        <span class="post-type-badge">{label}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Media display ──
    if media.media_type == 8:  # Carousel
        render_carousel(media, key)
    elif media.media_type == 2 and media.video_url:
        st.video(str(media.video_url))
    else:
        img_url = best_image_url(media)
        if img_url:
            st.image(img_url, use_container_width=True)

    # ── Caption ──
    if caption:
        short = caption[:120] + ("…" if len(caption) > 120 else "")
        st.markdown(f'<div class="post-caption">{short}</div>', unsafe_allow_html=True)

    # ── Download controls ──
    if len(all_items) == 1:
        label_dl, url, filename = all_items[0]
        try:
            data = fetch_bytes(url)
            st.download_button(
                f"⬇ Download {label_dl}",
                data=data,
                file_name=f"{media.pk}_{filename}",
                mime="video/mp4" if filename.endswith(".mp4") else "image/jpeg",
                key=f"dl_{key}_single"
            )
        except Exception as e:
            st.error(f"Download failed: {e}")
    elif len(all_items) > 1:
        # Individual buttons in columns
        cols = st.columns(min(len(all_items), 3))
        for i, (lbl, url, fname) in enumerate(all_items):
            with cols[i % len(cols)]:
                try:
                    data = fetch_bytes(url)
                    st.download_button(
                        f"⬇ {lbl}",
                        data=data,
                        file_name=f"{media.pk}_{fname}",
                        mime="video/mp4" if fname.endswith(".mp4") else "image/jpeg",
                        key=f"dl_{key}_{i}"
                    )
                except Exception:
                    st.caption(f"❌ {lbl}")
        # Download all as ZIP
        try:
            zip_data = make_zip(all_items)
            st.download_button(
                "⬇ Download All as ZIP",
                data=zip_data,
                file_name=f"{media.pk}_all.zip",
                mime="application/zip",
                key=f"dl_{key}_zip"
            )
        except Exception as e:
            st.error(f"ZIP failed: {e}")

    st.markdown("---")


def render_carousel(media: Media, key: str):
    """Render carousel with prev/next navigation using session state."""
    resources = media.resources
    n = len(resources)

    state_key = f"carousel_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = 0

    idx = st.session_state[state_key]
    res = resources[idx]

    # Display current item
    if res.media_type == 2 and res.video_url:
        st.video(str(res.video_url))
    else:
        img_url = best_image_url(res)
        if img_url:
            st.image(img_url, use_container_width=True)

    # Navigation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("◀", key=f"prev_{key}", disabled=(idx == 0)):
            st.session_state[state_key] = max(0, idx - 1)
            st.rerun()
    with col2:
        st.markdown(
            f"<p style='text-align:center;color:#888;font-size:0.8rem;margin:6px 0'>"
            f"{idx+1} / {n}</p>",
            unsafe_allow_html=True
        )
    with col3:
        if st.button("▶", key=f"next_{key}", disabled=(idx == n - 1)):
            st.session_state[state_key] = min(n - 1, idx + 1)
            st.rerun()


# ── Main UI ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="topbar">
  <span style="font-size:1.6rem"></span>
  <h1>SapZap</h1>
</div>
""", unsafe_allow_html=True)

# Session ID input (collapsed by default)
with st.expander("🔑 Session ID (required)", expanded="session_id" not in st.session_state):
    session_input = st.text_input(
        "Instagram Session ID",
        type="password",
        placeholder="Paste your sessionid cookie here",
        help="Get from browser cookies → instagram.com → sessionid",
        key="session_id_input"
    )
    if st.button("Save Session", key="save_session"):
        if session_input.strip():
            st.session_state["session_id"] = session_input.strip()
            st.success("Session saved ✓")
        else:
            st.error("Session ID cannot be empty")

session_id = st.session_state.get("session_id", "")

if not session_id:
    st.info("👆 Add your Instagram Session ID above to get started.")
    st.markdown("""
    **How to get your Session ID:**
    1. Open Instagram in desktop browser
    2. Login → Open DevTools (F12)
    3. Application → Cookies → `https://www.instagram.com`
    4. Copy the value of **`sessionid`**
    """)
    st.stop()

# Username input
col_u, col_b = st.columns([3, 1])
with col_u:
    username = st.text_input("Username", placeholder="e.g. natgeo", label_visibility="collapsed")
with col_b:
    fetch_btn = st.button("Fetch", type="primary")

# Load count
amount = st.select_slider(
    "Posts to load",
    options=[12, 24, 36, 50, 100],
    value=24,
    label_visibility="visible"
)

if fetch_btn and username.strip():
    uname = username.strip().lstrip("@")
    st.session_state["feed_username"] = uname
    st.session_state["feed_amount"] = amount
    st.session_state["feed_data"] = None  # reset

# ── Fetch & display feed ──────────────────────────────────────────────────────

if st.session_state.get("feed_username") and st.session_state.get("feed_data") is None:
    uname = st.session_state["feed_username"]
    amt = st.session_state.get("feed_amount", 24)

    with st.spinner(f"Connecting to Instagram…"):
        try:
            cl = get_client(session_id)
        except Exception as e:
            st.error(f"Session login failed: {e}")
            st.stop()

    with st.spinner(f"Loading @{uname}'s feed…"):
        try:
            user = cl.user_info_by_username(uname)
            medias = cl.user_medias(user.pk, amount=amt)
            st.session_state["feed_data"] = medias
            st.session_state["feed_user"] = user
        except Exception as e:
            st.error(f"Could not load feed: {e}")
            st.stop()

if st.session_state.get("feed_data"):
    medias = st.session_state["feed_data"]
    user = st.session_state.get("feed_user")

    # Profile header
    if user:
        pic_url = str(user.profile_pic_url) if user.profile_pic_url else ""
        c1, c2 = st.columns([1, 3])
        with c1:
            if pic_url:
                st.image(pic_url, width=72)
        with c2:
            st.markdown(f"**@{user.username}**")
            st.caption(f"{user.media_count} posts · {user.follower_count:,} followers")

        st.markdown(f"**{len(medias)} posts loaded**")
        st.markdown("---")

    for i, media in enumerate(medias):
        try:
            render_post(media, i)
        except Exception as e:
            st.warning(f"Could not render post {i+1}: {e}")
