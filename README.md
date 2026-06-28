# Instagram Downloader

Personal-use Instagram media downloader. Browse any feed and download photos, videos, and reels at full resolution.

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment — Streamlit Community Cloud (Free)

1. Push this folder to a **GitHub repo** (can be private)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub → select repo → `app.py` as main file
4. Click **Deploy**

That's it. Free, always-on, mobile-accessible via the generated URL.

## Authentication (recommended for full quality & restricted content)

Anonymous use only reaches public, lower-resolution media. For 1080×1920 reels,
age-restricted/sensitive accounts, private accounts you follow, stories, and
highlights, provide a Session ID one of two ways:

- **Per-session (UI):** paste it into the **Session ID** panel in the app.
- **App-wide (deploy):** set `IG_SESSIONID` in Streamlit Cloud **Secrets** (or a
  local `.streamlit/secrets.toml` — see `secrets.toml.example`) or as an
  environment variable. The app picks it up automatically; credentials are never
  hardcoded.

## Getting Your Session ID

1. Open [instagram.com](https://instagram.com) in desktop Chrome
2. Log in to your account
3. Press `F12` → **Application** tab → **Cookies** → `https://www.instagram.com`
4. Find the cookie named **`sessionid`** → copy its value
5. Paste into the app's Session ID field

> Session ID grants full account access. Keep it private. Do not share the app URL publicly.

## Features

- Full feed + reels for any public or private account
- Carousel/album navigation with per-item download
- Download All as ZIP for multi-media posts
- Highest resolution images and videos
- Mobile-first responsive design
- Session-based auth for private/age-restricted accounts
