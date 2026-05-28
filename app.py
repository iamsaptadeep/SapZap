import streamlit as st
import requests
import zipfile
import io
import time
import re
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, RateLimitError, ClientError

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

  .stSlider { padding: 0 4px; }

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

  /* ── URL download card ── */
  .url-card {
    background: #0d0d0d;
    border: 1px solid #2a2a2a;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 16px;
  }

  .stApp { background: #000 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_client(session_id: str) -> Client:
    cl = Client()
    cl.delay_range = [2, 4]          # wider delay → fewer rate-limit hits
    cl.login_by_sessionid(session_id)
    return cl


def api_call_with_retry(fn, *args, retries=3, base_wait=15, **kwargs):
    """Call fn(*args, **kwargs) with exponential backoff on rate-limit errors."""
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            msg = str(e).lower()
            is_rate = any(k in msg for k in ["wait a few minutes", "429", "rate", "please wait", "too many"])
            if is_rate and attempt < retries - 1:
                wait = base_wait * (2 ** attempt)
                st.toast(f"⏳ Rate limit hit — waiting {wait}s before retry {attempt+2}/{retries}…")
                time.sleep(wait)
            else:
                raise


def best_image_url(media) -> str:
    try:
        versions = media.image_versions2.get("candidates", [])
        if versions:
            return sorted(versions, key=lambda x: x.get("width", 0), reverse=True)[0]["url"]
    except Exception:
        pass
    if getattr(media, "thumbnail_url", None):
        return str(media.thumbnail_url)
    return ""


def all_video_versions(media) -> list[tuple[str, str, str]]:
    """
    Return [(url, label, filename), …] for every video version,
    1080×1920 first, then descending pixel count. Deduped by label.
    """
    try:
        versions = getattr(media, "video_versions", None) or []
        if not versions:
            url = str(getattr(media, "video_url", "") or "")
            return [(url, "HD", "video_HD.mp4")] if url else []

        def sort_key(v):
            w, h = v.get("width", 0), v.get("height", 0)
            is_full_hd = (w == 1080 and h == 1920) or (w == 1920 and h == 1080)
            return (1 if is_full_hd else 0, w * h)

        sorted_v = sorted(versions, key=sort_key, reverse=True)
        seen, result = set(), []
        for v in sorted_v:
            w, h = v.get("width", 0), v.get("height", 0)
            label = f"{w}×{h}" if (w and h) else "HD"
            if label in seen:
                continue
            seen.add(label)
            fname = f"video_{w}x{h}.mp4" if (w and h) else "video.mp4"
            result.append((v["url"], label, fname))
        return result
    except Exception:
        url = str(getattr(media, "video_url", "") or "")
        return [(url, "HD", "video_HD.mp4")] if url else []


def best_video_url(media) -> tuple[str, str]:
    versions = all_video_versions(media)
    if versions:
        return versions[0][0], versions[0][1]
    return "", "HD"


def fetch_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=90, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36",
        "Referer": "https://www.instagram.com/"
    })
    r.raise_for_status()
    return r.content


def media_type_label(media) -> tuple[str, str]:
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


# ── Carousel renderer ─────────────────────────────────────────────────────────

def render_carousel(media, key: str):
    resources = media.resources
    n         = len(resources)
    sk        = f"carousel_{key}"
    if sk not in st.session_state:
        st.session_state[sk] = 0
    idx = st.session_state[sk]
    res = resources[idx]

    if res.media_type == 2:
        vurl, _ = best_video_url(res)
        if vurl: st.video(vurl)
    else:
        img_url = best_image_url(res)
        if img_url: st.image(img_url, use_container_width=True)

    st.markdown(f'<div class="carousel-counter">{idx+1} / {n}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("◀ Prev", key=f"prev_{key}", disabled=(idx == 0), use_container_width=True):
            st.session_state[sk] = max(0, idx - 1); st.rerun()
    with c2:
        if st.button("Next ▶", key=f"next_{key}", disabled=(idx == n-1), use_container_width=True):
            st.session_state[sk] = min(n-1, idx + 1); st.rerun()


# ── Download buttons (reusable) ───────────────────────────────────────────────

def render_download_buttons(media, all_items: list, key: str, is_reel_mode: bool = False):
    """Render download button(s). Reels get one button per resolution (stacked)."""
    if not all_items:
        st.caption("No downloadable media found.")
        return

    if is_reel_mode or (len(all_items) > 0 and media.media_type == 2):
        # Stack one button per resolution
        for i, (lbl, url, fname, rlabel) in enumerate(all_items):
            star = " ⭐ Best" if i == 0 else ""
            btn_label = f"⬇ {rlabel}{star}"
            try:
                data = fetch_bytes(url)
                st.download_button(
                    btn_label, data=data,
                    file_name=f"{media.pk}_{fname}",
                    mime="video/mp4",
                    key=f"dl_{key}_res{i}",
                    use_container_width=True
                )
            except Exception:
                st.caption(f"❌ {rlabel} unavailable")
    elif len(all_items) == 1:
        lbl, url, fname, rlabel = all_items[0]
        res_info = f" · {rlabel}" if rlabel else ""
        try:
            data = fetch_bytes(url)
            st.download_button(
                f"⬇ Download{res_info}", data=data,
                file_name=f"{media.pk}_{fname}",
                mime="video/mp4" if fname.endswith(".mp4") else "image/jpeg",
                key=f"dl_{key}_single",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Download failed: {e}")
    else:
        # Album: 2-column grid + ZIP
        cols = st.columns(2)
        for i, (lbl, url, fname, rlabel) in enumerate(all_items):
            with cols[i % 2]:
                try:
                    data = fetch_bytes(url)
                    st.download_button(
                        f"⬇ {lbl}", data=data,
                        file_name=f"{media.pk}_{fname}",
                        mime="video/mp4" if fname.endswith(".mp4") else "image/jpeg",
                        key=f"dl_{key}_{i}",
                        use_container_width=True
                    )
                except Exception:
                    st.caption(f"❌ {lbl}")
        try:
            st.download_button(
                "⬇ Download All as ZIP", data=make_zip(all_items),
                file_name=f"{media.pk}_all.zip", mime="application/zip",
                key=f"dl_{key}_zip", use_container_width=True
            )
        except Exception as e:
            st.error(f"ZIP failed: {e}")


# ── Post / Reel card renderer ─────────────────────────────────────────────────

def render_post(media, idx: int, show_reel_aspect: bool = False):
    key       = f"post_{idx}_{media.pk}"
    is_vid    = media.media_type == 2
    label, badge_cls = media_type_label(media)
    username  = media.user.username if media.user else "unknown"
    caption   = media.caption_text or ""

    # Build download items
    if is_vid:
        all_items = [(f"⬇ {rl}", url, fn, rl) for url, rl, fn in all_video_versions(media)]
    elif media.media_type == 8:
        all_items = []
        for i, res in enumerate(media.resources):
            if res.media_type == 2:
                for url, rl, fn in all_video_versions(res):
                    all_items.append((f"Video {i+1} {rl}", url, f"v{i+1}_{fn}", rl))
            else:
                img_url = best_image_url(res)
                if img_url:
                    all_items.append((f"Photo {i+1}", img_url, f"photo_{i+1}.jpg", ""))
    else:
        img_url = best_image_url(media)
        all_items = [("Photo", img_url, "photo.jpg", "")] if img_url else []

    # Card header (pure HTML — no Streamlit widgets inside)
    st.markdown(f"""
    <div class="post-card">
      <div class="post-header">
        <span class="post-username">@{username}</span>
        <span class="post-badge {badge_cls}">{label}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Media preview
    if media.media_type == 8:
        render_carousel(media, key)
    elif is_vid:
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
    render_download_buttons(media, all_items, key, is_reel_mode=show_reel_aspect and is_vid)
    st.markdown("---")


# ── URL downloader section ────────────────────────────────────────────────────

def render_url_downloader(cl: Client):
    st.markdown("### 🔗 Download by URL")
    st.caption("Paste any Instagram post, reel, or video link below.")

    url_input = st.text_input(
        "Instagram URL",
        placeholder="https://www.instagram.com/reel/ABC123/",
        label_visibility="collapsed",
        key="url_dl_input"
    )
    fetch_url_btn = st.button("⚡ Fetch & Download", type="primary", key="url_dl_btn")

    if fetch_url_btn and url_input.strip():
        raw_url = url_input.strip()
        with st.spinner("Fetching media info…"):
            try:
                pk = api_call_with_retry(cl.media_pk_from_url, raw_url)
                media = api_call_with_retry(cl.media_info, pk)
            except Exception as e:
                err = str(e)
                if "wait a few minutes" in err.lower() or "please wait" in err.lower():
                    st.error("⏳ Instagram rate limit reached. Please wait 2–5 minutes and try again.")
                else:
                    st.error(f"Could not fetch URL: {err}")
                return

        st.success("Media found!")
        render_post(media, idx=99999, show_reel_aspect=is_reel(media))


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
            st.rerun()
        else:
            st.error("Session ID cannot be empty")

session_id = st.session_state.get("session_id", "")

if not session_id:
    st.info("👆 Add your Instagram Session ID to get started.")
    st.markdown("""
**How to get Session ID:**
1. Open Instagram in a desktop browser and log in
2. Press **F12** → Application → Cookies → `instagram.com`
3. Copy the value of **`sessionid`**
    """)
    st.stop()

# Establish client once
try:
    cl = get_client(session_id)
except Exception as e:
    st.error(f"Session login failed — check your Session ID. ({e})")
    st.stop()

# ── Top-level tab: By URL | Browse Profile ────────────────────────────────────
main_tab = st.session_state.get("main_tab", "url")

col_m1, col_m2 = st.columns(2)
with col_m1:
    if st.button("🔗 Download by URL",
                 use_container_width=True,
                 type="primary" if main_tab == "url" else "secondary",
                 key="main_tab_url"):
        st.session_state["main_tab"] = "url"
        st.rerun()
with col_m2:
    if st.button("👤 Browse Profile",
                 use_container_width=True,
                 type="primary" if main_tab == "profile" else "secondary",
                 key="main_tab_profile"):
        st.session_state["main_tab"] = "profile"
        st.rerun()

st.markdown("---")

# ═══════════════════════════════════════════════════════
# TAB A: Download by URL
# ═══════════════════════════════════════════════════════
if main_tab == "url":
    render_url_downloader(cl)

# ═══════════════════════════════════════════════════════
# TAB B: Browse Profile
# ═══════════════════════════════════════════════════════
else:
    # ── Username + Fetch ──────────────────────────────
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
        st.session_state["feed_amount"]   = amount
        st.session_state["feed_data"]     = None
        st.session_state["reels_data"]    = None
        st.session_state["feed_user"]     = None

    # ── Fetch data ──────────────────────────────────
    if st.session_state.get("feed_username") and st.session_state.get("feed_data") is None:
        uname = st.session_state["feed_username"]
        amt   = st.session_state.get("feed_amount", 24)

        with st.spinner(f"Loading @{uname}'s content…"):
            try:
                user = api_call_with_retry(cl.user_info_by_username, uname)
                st.session_state["feed_user"] = user
                uid  = user.pk

                # ── Fetch posts (photos, albums, non-reel videos) ──
                raw_medias = api_call_with_retry(cl.user_medias, uid, amount=amt)
                posts = [m for m in raw_medias if not is_reel(m)]

                # ── Fetch reels via dedicated endpoint ──
                # user_clips is the correct endpoint for Reels
                reels = []
                try:
                    reels = api_call_with_retry(cl.user_clips, uid, amount=min(amt, 50))
                except Exception as clips_err:
                    # fallback: pull reels that appeared in user_medias
                    reels = [m for m in raw_medias if is_reel(m)]
                    st.toast(f"ℹ️ Reel endpoint limited — showing {len(reels)} reels from feed.")

                # Deduplicate reels by pk
                seen_pks = set()
                unique_reels = []
                for r in reels:
                    if r.pk not in seen_pks:
                        unique_reels.append(r)
                        seen_pks.add(r.pk)
                reels = unique_reels

                st.session_state["feed_data"]  = posts
                st.session_state["reels_data"] = reels

            except Exception as e:
                err = str(e)
                if "wait a few minutes" in err.lower() or "please wait" in err.lower():
                    st.error(
                        "⏳ **Instagram rate limit reached.**\n\n"
                        "Instagram is throttling requests. Please wait **2–5 minutes** "
                        "then tap Fetch again. Avoid fetching large amounts (100 posts) "
                        "repeatedly — use 12–24 to stay within limits."
                    )
                else:
                    st.error(f"Could not load content: {err}")
                st.stop()

    # ── Display ─────────────────────────────────────
    if st.session_state.get("feed_data") is not None:
        posts  = st.session_state.get("feed_data") or []
        reels  = st.session_state.get("reels_data") or []
        user   = st.session_state.get("feed_user")

        # Profile header
        if user:
            c1, c2 = st.columns([1, 4])
            with c1:
                pic = str(user.profile_pic_url) if user.profile_pic_url else ""
                if pic: st.image(pic, width=64)
            with c2:
                st.markdown(f"**@{user.username}**")
                st.caption(f"{user.media_count:,} posts · {user.follower_count:,} followers")
            st.markdown("---")

        # Sub-tab: Posts | Reels
        sub_tab = st.session_state.get("sub_tab", "posts")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"📷 Posts ({len(posts)})",
                         use_container_width=True,
                         type="primary" if sub_tab == "posts" else "secondary",
                         key="sub_tab_posts"):
                st.session_state["sub_tab"] = "posts"; st.rerun()
        with c2:
            if st.button(f"🎬 Reels ({len(reels)})",
                         use_container_width=True,
                         type="primary" if sub_tab == "reels" else "secondary",
                         key="sub_tab_reels"):
                st.session_state["sub_tab"] = "reels"; st.rerun()

        st.markdown("---")

        if sub_tab == "posts":
            if not posts:
                st.info("No posts found for this account.")
            else:
                st.markdown(f'<p class="section-label">📷 {len(posts)} Posts</p>', unsafe_allow_html=True)
                for i, media in enumerate(posts):
                    try:
                        render_post(media, i, show_reel_aspect=False)
                    except Exception as e:
                        st.warning(f"Could not render post {i+1}: {e}")

        else:  # reels
            if not reels:
                st.info("No reels found. This account may have no reels, or try refreshing.")
            else:
                st.markdown(f'<p class="section-label">🎬 {len(reels)} Reels — all resolutions shown</p>',
                            unsafe_allow_html=True)
                for i, media in enumerate(reels):
                    try:
                        render_post(media, i + 10000, show_reel_aspect=True)
                    except Exception as e:
                        st.warning(f"Could not render reel {i+1}: {e}")
