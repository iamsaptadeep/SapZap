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
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CSS (Mobile-first, Samsung S24 optimised) ────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', -apple-system, sans-serif;
    -webkit-text-size-adjust: 100%;
    touch-action: manipulation;
  }

  /* Full-width on mobile, capped on desktop */
  .block-container {
    padding: 0.5rem 0.75rem 4rem !important;
    max-width: 500px !important;
    margin: auto !important;
  }

  /* Hide Streamlit chrome */
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

  /* ── Tab bar ── */
  .tab-bar {
    display: flex;
    gap: 0;
    border-bottom: 1px solid #262626;
    margin-bottom: 16px;
  }
  .tab-btn {
    flex: 1;
    text-align: center;
    padding: 10px 0;
    font-size: 0.8rem;
    font-weight: 600;
    color: #888;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    border-bottom: 2px solid transparent;
    cursor: pointer;
  }
  .tab-btn.active {
    color: #fff;
    border-bottom-color: #fff;
  }

  /* ── Profile header ── */
  .profile-wrap {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 0 14px;
    border-bottom: 1px solid #262626;
    margin-bottom: 16px;
  }
  .profile-pic {
    width: 64px; height: 64px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #333;
  }
  .profile-info { flex: 1; }
  .profile-username { font-size: 1rem; font-weight: 700; color: #fff; margin: 0 0 2px; }
  .profile-meta { font-size: 0.78rem; color: #aaa; }

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
  .post-avatar {
    width: 30px; height: 30px;
    border-radius: 50%;
    object-fit: cover;
  }
  .post-username {
    font-size: 0.85rem; font-weight: 600; color: #fff;
    flex: 1; min-width: 0;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .post-badge {
    flex-shrink: 0;
    margin-left: 8px;
    font-size: 0.65rem; font-weight: 700;
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

  /* ── Media area ── */
  .media-wrap {
    background: #000;
    width: 100%;
    aspect-ratio: 1;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .media-wrap img, .media-wrap video {
    width: 100%; height: 100%;
    object-fit: contain;
  }
  /* Reels: portrait 9:16 */
  .reel-wrap {
    background: #000;
    width: 100%;
    aspect-ratio: 9/16;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .reel-wrap video {
    width: 100%; height: 100%;
    object-fit: contain;
  }

  /* ── Carousel nav ── */
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
    min-height: 44px !important;      /* iOS touch target */
    -webkit-tap-highlight-color: transparent;
  }
  .stDownloadButton > button:hover {
    opacity: 0.9 !important;
  }
  div[data-testid="stHorizontalBlock"] .stDownloadButton > button {
    font-size: 0.75rem !important;
    padding: 9px 8px !important;
    border-radius: 8px !important;
  }

  /* ── Primary action button ── */
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

  /* ── Slider ── */
  .stSlider { padding: 0 4px; }

  /* ── Expander ── */
  .streamlit-expanderHeader {
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    min-height: 44px !important;
  }

  /* ── Divider ── */
  hr { border-color: #1a1a1a !important; margin: 8px 0 16px !important; }

  /* ── Info / error boxes ── */
  .stAlert { border-radius: 10px !important; font-size: 0.85rem !important; }

  /* ── Spinner text ── */
  .stSpinner { font-size: 0.88rem; color: #888; }

  /* ── Resolution badge ── */
  .res-badge {
    display: inline-block;
    font-size: 0.65rem; font-weight: 700;
    background: #1c2a1c; color: #56d364;
    border-radius: 4px; padding: 1px 5px;
    margin-left: 4px; vertical-align: middle;
  }

  /* ── Section heading ── */
  .section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #666;
    margin: 0 0 10px;
  }

  /* Dark overall background */
  .stApp { background: #000 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_client(session_id: str) -> Client:
    cl = Client()
    cl.delay_range = [1, 2]
    cl.login_by_sessionid(session_id)
    return cl


def best_image_url(media) -> str:
    try:
        versions = media.image_versions2.get("candidates", [])
        if versions:
            best = sorted(versions, key=lambda x: x.get("width", 0), reverse=True)[0]
            return best["url"]
    except Exception:
        pass
    if getattr(media, "thumbnail_url", None):
        return str(media.thumbnail_url)
    return ""


def best_video_url(media) -> tuple[str, str]:
    """
    Return (url, resolution_label) for the best-quality video.
    Prefers 1080×1920 (portrait reel). Falls back to highest total pixels.
    """
    try:
        versions = getattr(media, "video_versions", None) or []
        if versions:
            # Prefer exact 1080×1920 or 1920×1080
            for v in versions:
                w, h = v.get("width", 0), v.get("height", 0)
                if (w == 1080 and h == 1920) or (w == 1920 and h == 1080):
                    return v["url"], f"{w}×{h}"
            # Fallback: highest total pixels
            sorted_v = sorted(
                versions,
                key=lambda v: (v.get("width", 0) * v.get("height", 0)),
                reverse=True
            )
            best = sorted_v[0]
            w = best.get("width", 0)
            h = best.get("height", 0)
            label = f"{w}×{h}" if w and h else "HD"
            return best["url"], label
    except Exception:
        pass
    url = str(getattr(media, "video_url", "") or "")
    return url, "HD"


def all_video_versions(media) -> list[tuple[str, str, str]]:
    """
    Return list of (url, resolution_label, filename) for ALL video versions,
    sorted best-first (1080×1920 at top, then by descending pixel count).
    Deduplicates by resolution label.
    """
    try:
        versions = getattr(media, "video_versions", None) or []
        if not versions:
            url = str(getattr(media, "video_url", "") or "")
            return [(url, "HD", "video_HD.mp4")] if url else []

        def sort_key(v):
            w, h = v.get("width", 0), v.get("height", 0)
            # Give 1080×1920 and 1920×1080 top priority
            is_preferred = (w == 1080 and h == 1920) or (w == 1920 and h == 1080)
            return (1 if is_preferred else 0, w * h)

        sorted_v = sorted(versions, key=sort_key, reverse=True)
        seen_labels = set()
        result = []
        for v in sorted_v:
            w, h = v.get("width", 0), v.get("height", 0)
            label = f"{w}×{h}" if w and h else "HD"
            if label in seen_labels:
                continue
            seen_labels.add(label)
            fname = f"video_{w}x{h}.mp4" if w and h else "video.mp4"
            result.append((v["url"], label, fname))
        return result
    except Exception:
        url = str(getattr(media, "video_url", "") or "")
        return [(url, "HD", "video_HD.mp4")] if url else []


def fetch_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=60, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36",
        "Referer": "https://www.instagram.com/"
    })
    r.raise_for_status()
    return r.content


def media_type_label(media) -> tuple[str, str]:
    """Return (label, badge_class)."""
    t = media.media_type
    pt = (getattr(media, "product_type", "") or "").lower()
    if t == 1:
        return "Photo", "badge-photo"
    if t == 2:
        if "reel" in pt or "clips" in pt:
            return "Reel", "badge-reel"
        return "Video", "badge-video"
    if t == 8:
        return f"Album · {len(media.resources)}", "badge-album"
    return "Post", "badge-photo"


def is_reel(media) -> bool:
    pt = (getattr(media, "product_type", "") or "").lower()
    return media.media_type == 2 and ("reel" in pt or "clips" in pt)


def get_all_items(media, include_all_resolutions: bool = False):
    """Return list of (label, url, filename, res_label) for all items.
    When include_all_resolutions=True, video items include every available
    resolution as a separate entry (best first).
    """
    items = []
    if media.media_type == 8:
        for i, res in enumerate(media.resources):
            if res.media_type == 2:
                if include_all_resolutions:
                    versions = all_video_versions(res)
                    for url, rlabel, fname in versions:
                        items.append((f"Video {i+1} {rlabel}", url, f"video_{i+1}_{fname}", rlabel))
                else:
                    vurl, rlabel = best_video_url(res)
                    if not vurl:
                        vurl = str(getattr(res, "video_url", "") or "")
                    if vurl:
                        items.append((f"Video {i+1}", vurl, f"video_{i+1}.mp4", rlabel))
            else:
                img_url = best_image_url(res)
                if img_url:
                    items.append((f"Photo {i+1}", img_url, f"photo_{i+1}.jpg", ""))
    elif media.media_type == 2:
        if include_all_resolutions:
            versions = all_video_versions(media)
            for url, rlabel, fname in versions:
                items.append((f"⬇ {rlabel}", url, fname, rlabel))
        else:
            vurl, rlabel = best_video_url(media)
            if not vurl:
                vurl = str(getattr(media, "video_url", "") or "")
            if vurl:
                items.append(("Video", vurl, "video.mp4", rlabel))
    else:
        img_url = best_image_url(media)
        if img_url:
            items.append(("Photo", img_url, "photo.jpg", ""))
    return items


def make_zip(items: list) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for label, url, filename, _ in items:
            try:
                data = fetch_bytes(url)
                zf.writestr(filename, data)
            except Exception:
                pass
    buf.seek(0)
    return buf.read()


# ── Carousel renderer ─────────────────────────────────────────────────────────

def render_carousel(media, key: str):
    resources = media.resources
    n = len(resources)
    state_key = f"carousel_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = 0

    idx = st.session_state[state_key]
    res = resources[idx]

    if res.media_type == 2:
        vurl, _ = best_video_url(res)
        if not vurl:
            vurl = str(getattr(res, "video_url", "") or "")
        if vurl:
            st.video(vurl)
    else:
        img_url = best_image_url(res)
        if img_url:
            st.image(img_url, use_container_width=True)

    st.markdown(
        f'<div class="carousel-counter">{idx+1} / {n}</div>',
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("◀ Prev", key=f"prev_{key}", disabled=(idx == 0), use_container_width=True):
            st.session_state[state_key] = max(0, idx - 1)
            st.rerun()
    with col2:
        if st.button("Next ▶", key=f"next_{key}", disabled=(idx == n - 1), use_container_width=True):
            st.session_state[state_key] = min(n - 1, idx + 1)
            st.rerun()


# ── Post renderer ─────────────────────────────────────────────────────────────

def render_post(media, idx: int, show_reel_aspect: bool = False, include_all_resolutions: bool = False):
    key = f"post_{idx}_{media.pk}"
    all_items = get_all_items(media, include_all_resolutions=include_all_resolutions)
    caption = media.caption_text or ""
    label, badge_cls = media_type_label(media)

    username = media.user.username if media.user else "unknown"

    st.markdown(f"""
    <div class="post-card">
      <div class="post-header">
        <span class="post-username">@{username}</span>
        <span class="post-badge {badge_cls}">{label}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Media display
    if media.media_type == 8:
        render_carousel(media, key)
    elif media.media_type == 2:
        vurl, res_label = best_video_url(media)
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
                    f'<div style="text-align:right;padding:2px 10px 4px">'
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

    # Download controls
    if len(all_items) == 1:
        lbl, url, fname, rlabel = all_items[0]
        res_info = f" · {rlabel}" if rlabel else ""
        try:
            data = fetch_bytes(url)
            st.download_button(
                f"⬇ Download {lbl}{res_info}",
                data=data,
                file_name=f"{media.pk}_{fname}",
                mime="video/mp4" if fname.endswith(".mp4") else "image/jpeg",
                key=f"dl_{key}_single",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Download failed: {e}")
    elif len(all_items) > 1:
        # For reels with multiple resolutions: stack vertically (one per row on mobile)
        # For albums/carousels with multiple files: use 2-column grid
        is_multi_res = include_all_resolutions and media.media_type == 2
        if is_multi_res:
            # Resolution options stacked — label shows "Best Quality" for first
            for i, (lbl, url, fname, rlabel) in enumerate(all_items):
                display_lbl = f"⬇ Download {rlabel}" + (" ✦ Best" if i == 0 else "")
                try:
                    data = fetch_bytes(url)
                    st.download_button(
                        display_lbl,
                        data=data,
                        file_name=f"{media.pk}_{fname}",
                        mime="video/mp4",
                        key=f"dl_{key}_{i}",
                        use_container_width=True
                    )
                except Exception:
                    st.caption(f"❌ {rlabel} unavailable")
        else:
            cols = st.columns(min(len(all_items), 2))
            for i, (lbl, url, fname, rlabel) in enumerate(all_items):
                with cols[i % len(cols)]:
                    try:
                        data = fetch_bytes(url)
                        st.download_button(
                            f"⬇ {lbl}",
                            data=data,
                            file_name=f"{media.pk}_{fname}",
                            mime="video/mp4" if fname.endswith(".mp4") else "image/jpeg",
                            key=f"dl_{key}_{i}",
                            use_container_width=True
                        )
                    except Exception:
                        st.caption(f"❌ {lbl}")

            try:
                zip_data = make_zip(all_items)
                st.download_button(
                    "⬇ Download All as ZIP",
                    data=zip_data,
                    file_name=f"{media.pk}_all.zip",
                    mime="application/zip",
                    key=f"dl_{key}_zip",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"ZIP failed: {e}")

    st.markdown("---")


# ── Main UI ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="topbar">
  <span style="font-size:1.8rem">⚡</span>
  <h1>SapZap</h1>
</div>
""", unsafe_allow_html=True)

# ── Session ID ────────────────────────────────────────────────────────────────
with st.expander("🔑 Session ID (required)", expanded="session_id" not in st.session_state):
    session_input = st.text_input(
        "Instagram Session ID",
        type="password",
        placeholder="Paste sessionid cookie here",
        help="Browser → instagram.com → DevTools → Application → Cookies → sessionid",
        key="session_id_input"
    )
    if st.button("💾 Save Session", key="save_session"):
        if session_input.strip():
            st.session_state["session_id"] = session_input.strip()
            st.success("Session saved ✓")
        else:
            st.error("Session ID cannot be empty")

session_id = st.session_state.get("session_id", "")

if not session_id:
    st.info("👆 Add your Instagram Session ID to get started.")
    st.markdown("""
**How to get Session ID:**
1. Open Instagram on desktop browser & login
2. Press **F12** → Application → Cookies → `instagram.com`
3. Copy the value of **`sessionid`**
    """)
    st.stop()

# ── Username + Fetch ──────────────────────────────────────────────────────────
col_u, col_b = st.columns([3, 1])
with col_u:
    username = st.text_input(
        "Username",
        placeholder="e.g. natgeo",
        label_visibility="collapsed",
        key="username_input"
    )
with col_b:
    fetch_btn = st.button("Fetch", type="primary")

amount = st.select_slider(
    "Posts to load",
    options=[12, 24, 36, 50, 100],
    value=24,
)

if fetch_btn and username.strip():
    uname = username.strip().lstrip("@")
    st.session_state["feed_username"] = uname
    st.session_state["feed_amount"] = amount
    st.session_state["feed_data"] = None
    st.session_state["reels_data"] = None

# ── Fetch data ────────────────────────────────────────────────────────────────

if st.session_state.get("feed_username") and st.session_state.get("feed_data") is None:
    uname = st.session_state["feed_username"]
    amt = st.session_state.get("feed_amount", 24)

    with st.spinner("Connecting to Instagram…"):
        try:
            cl = get_client(session_id)
        except Exception as e:
            st.error(f"Session login failed: {e}")
            st.stop()

    with st.spinner(f"Loading @{uname}'s content…"):
        try:
            user = cl.user_info_by_username(uname)
            st.session_state["feed_user"] = user

            # Fetch all medias
            all_medias = cl.user_medias(user.pk, amount=amt)

            # Split posts vs reels
            posts = []
            reels = []
            for m in all_medias:
                if is_reel(m):
                    reels.append(m)
                else:
                    posts.append(m)

            # Also fetch dedicated reels if available
            try:
                reel_medias = cl.user_clips(user.pk, amount=min(amt, 50))
                # Deduplicate by pk
                existing_pks = {r.pk for r in reels}
                for r in reel_medias:
                    if r.pk not in existing_pks:
                        reels.append(r)
                        existing_pks.add(r.pk)
            except Exception:
                pass  # user_clips not available for all accounts

            st.session_state["feed_data"] = posts
            st.session_state["reels_data"] = reels

        except Exception as e:
            st.error(f"Could not load content: {e}")
            st.stop()

# ── Display ───────────────────────────────────────────────────────────────────

if st.session_state.get("feed_data") is not None or st.session_state.get("reels_data") is not None:
    posts = st.session_state.get("feed_data") or []
    reels = st.session_state.get("reels_data") or []
    user  = st.session_state.get("feed_user")

    # ── Profile header ──
    if user:
        pic_url = str(user.profile_pic_url) if user.profile_pic_url else ""
        c1, c2 = st.columns([1, 4])
        with c1:
            if pic_url:
                st.image(pic_url, width=64)
        with c2:
            st.markdown(f"**@{user.username}**")
            st.caption(f"{user.media_count:,} posts · {user.follower_count:,} followers")

        st.markdown("---")

    # ── Tab selection ──
    tab_key = "active_tab"
    if tab_key not in st.session_state:
        st.session_state[tab_key] = "posts"

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        posts_active = "active" if st.session_state[tab_key] == "posts" else ""
        if st.button(
            f"📷 Posts ({len(posts)})",
            key="tab_posts",
            use_container_width=True,
            type="primary" if st.session_state[tab_key] == "posts" else "secondary"
        ):
            st.session_state[tab_key] = "posts"
            st.rerun()
    with col_t2:
        if st.button(
            f"🎬 Reels ({len(reels)})",
            key="tab_reels",
            use_container_width=True,
            type="primary" if st.session_state[tab_key] == "reels" else "secondary"
        ):
            st.session_state[tab_key] = "reels"
            st.rerun()

    st.markdown("---")

    # ── Posts tab ──
    if st.session_state[tab_key] == "posts":
        if not posts:
            st.info("No posts found for this account.")
        else:
            st.markdown(f'<p class="section-label">📷 {len(posts)} Posts</p>', unsafe_allow_html=True)
            for i, media in enumerate(posts):
                try:
                    render_post(media, i, show_reel_aspect=False)
                except Exception as e:
                    st.warning(f"Could not render post {i+1}: {e}")

    # ── Reels tab ──
    elif st.session_state[tab_key] == "reels":
        if not reels:
            st.info("No reels found for this account (or account is private).")
        else:
            st.markdown(f'<p class="section-label">🎬 {len(reels)} Reels · Highest available resolution</p>', unsafe_allow_html=True)
            for i, media in enumerate(reels):
                try:
                    render_post(media, i + 10000, show_reel_aspect=True, include_all_resolutions=True)
                except Exception as e:
                    st.warning(f"Could not render reel {i+1}: {e}")




                    