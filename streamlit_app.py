# streamlit_app.py
import streamlit as st
import datetime, time, threading, json, os
from typing import List, Dict
import requests

# ---------- CONFIG ----------
# The real API keys and tokens MUST be placed in Streamlit secrets (preferred)
# Example secrets keys:
# OPENAI_API_KEY, META_PAGE_ACCESS_TOKEN, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET,
# TIKTOK_CLIENT_KEY, GOOGLE_DRIVE_CREDENTIALS_JSON (or use service account)
#
# For local testing you can also set environment variables or a .env file (not recommended for cloud)

# ---------- Utilities ----------
def load_sample_trends() -> List[Dict]:
    # Example seed trending posts (will be replaced with real trend fetcher)
    return [
        {"title":"Top Safari Lodges in Queen Elizabeth NP",
         "summary":"A quick guide to the best safari lodges combining comfort and views.",
         "tags":["#Uganda","#Safari","#Wildlife","#NielsUg"]},
        {"title":"Murchison Falls: What to Expect",
         "summary":"The roar of the falls and where to get the best photos.",
         "tags":["#MurchisonFalls","#Travel","#NielsUg"]}
    ]

def generate_caption_with_openai(title: str, summary: str) -> str:
    """
    Uses OpenAI to generate caption. Requires OPENAI_API_KEY in secrets or environment.
    If you don't want OpenAI, you can use this fallback simple join.
    """
    openai_key = st.secrets.get("OPENAI_API_KEY", None)
    if not openai_key:
        # fallback simple caption
        return f"{title} — {summary} {' '.join(['#Travel','#Wildlife','#NielsUg'])}"
    # Minimal OpenAI call (text generation) - keep small to save tokens
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {openai_key}"}
    data = {
        "model":"gpt-4o-mini",            # change to available model if needed
        "messages":[{"role":"system","content":"You are a social media copywriter for tourism."},
                    {"role":"user","content":f"Write 1 short Instagram caption for: {title} — {summary}. Add 6 relevant hashtags."}],
        "max_tokens":120,
        "temperature":0.7
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=15)
        r.raise_for_status()
        resp = r.json()
        # compatibility: extract text
        text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not text:
            text = resp.get("choices", [{}])[0].get("text","")
        return text.strip()
    except Exception as e:
        st.warning(f"OpenAI call failed: {e}. Using fallback caption.")
        return f"{title} — {summary} {' '.join(['#Travel','#Wildlife','#NielsUg'])}"

# ---------- Placeholder platform posting functions ----------
def post_to_facebook_instagram(image_path: str, caption: str) -> Dict:
    """
    Placeholder: implement Meta Graph API upload with PAGE_ACCESS_TOKEN.
    Returns a dict with status and platform response.
    """
    # Example: return {"status":"ok","platform":"facebook","id":"12345"}
    st.info("post_to_facebook_instagram() called (placeholder). Add real Meta API code here.")
    return {"status":"mocked","platform":"facebook_instagram"}

def post_to_youtube(video_path: str, title: str, description: str) -> Dict:
    """
    Placeholder: implement YouTube Data API v3 upload (OAuth).
    """
    st.info("post_to_youtube() called (placeholder). Add YouTube upload code here.")
    return {"status":"mocked","platform":"youtube"}

def post_to_tiktok(video_path: str, caption: str) -> Dict:
    """
    Placeholder: implement TikTok Business API or upload automation.
    """
    st.info("post_to_tiktok() called (placeholder). Add TikTok upload code here.")
    return {"status":"mocked","platform":"tiktok"}

# ---------- Scheduler ----------
class SchedulerThread(threading.Thread):
    def __init__(self, interval_seconds:int=60):
        super().__init__(daemon=True)
        self.interval = interval_seconds
        self._stop = threading.Event()
    def run(self):
        while not self._stop.is_set():
            try:
                # check scheduled queue
                # For demo: nothing runs automatically; real code reads schedule.json and posts if time reached
                time.sleep(self.interval)
            except Exception as e:
                print("Scheduler error:", e)
    def stop(self):
        self._stop.set()

sched_thread = None

# ---------- Streamlit UI ----------
st.set_page_config(page_title="NIELS-UG AGENT — Online", layout="wide")
st.title("NIELS-UG AGENT — Tourism & Wildlife Auto-Poster")
st.write("Welcome, **Niels ug** — your online agent for tourism, hotels and national parks content.")

# Sidebar: scheduling & platforms
with st.sidebar:
    st.header("Agent Settings")
    daily_time = st.time_input("Daily posting time (local)", value=datetime.time(9,0))
    auto_post = st.checkbox("Enable automatic posting (WARNING: configure API keys first!)", value=False)
    st.markdown("**Platforms to post to:**")
    to_instagram = st.checkbox("Instagram", value=True)
    to_facebook = st.checkbox("Facebook", value=True)
    to_tiktok = st.checkbox("TikTok", value=False)
    to_youtube = st.checkbox("YouTube", value=False)
    if st.button("Start Scheduler"):
        if not st.session_state.get("scheduler_running", False):
            st.session_state["scheduler_running"] = True
            # start scheduler thread
            if not globals().get("sched_thread"):
                globals()["sched_thread"] = SchedulerThread()
                globals()["sched_thread"].start()
            st.success("Scheduler started (demo mode).")
    if st.button("Stop Scheduler"):
        if st.session_state.get("scheduler_running", False):
            st.session_state["scheduler_running"] = False
            if globals().get("sched_thread"):
                globals()["sched_thread"].stop()
            st.warning("Scheduler stopped.")

# Main: show trending ideas
st.header("Trending post ideas (sample)")
trends = load_sample_trends()
for idx,t in enumerate(trends):
    st.subheader(f"{idx+1}. {t['title']}")
    st.write(t['summary'])
    tags_line = " ".join(t.get("tags",[]))
    st.write("Tags:", tags_line)
    caption = generate_caption_with_openai(t['title'], t['summary'])
    st.text_area(f"Generated caption (editable) for item {idx+1}", value=caption, key=f"cap_{idx}")

    # Upload media or pick from Drive (for demo we skip)
    media_path = st.text_input(f"Local media path or Drive link for item {idx+1} (optional)", key=f"media_{idx}")

    cols = st.columns(4)
    if cols[0].button("Simulate post to selected platforms", key=f"sim_{idx}"):
        selected = []
        if to_instagram: selected.append("Instagram")
        if to_facebook: selected.append("Facebook")
        if to_tiktok: selected.append("TikTok")
        if to_youtube: selected.append("YouTube")
        st.success(f"Simulated posting to: {', '.join(selected)}")
    if cols[1].button("Post to Facebook/Instagram (mock)", key=f"fb_{idx}"):
        res = post_to_facebook_instagram(media_path, caption)
        st.json(res)
    if cols[2].button("Post to YouTube (mock)", key=f"yt_{idx}"):
        res = post_to_youtube(media_path, t['title'], caption)
        st.json(res)
    if cols[3].button("Post to TikTok (mock)", key=f"tt_{idx}"):
        res = post_to_tiktok(media_path, caption)
        st.json(res)
    st.markdown("---")

st.info("To make these real: configure Streamlit Secrets with OPENAI, META, YOUTUBE, TIKTOK credentials and replace the placeholder functions with actual API calls. I will help with each step.")
