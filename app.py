"""
Streamlit Frontend for Call Transcription and Zoho Integration

Two options:
  1. Download → Transcribe → Edit → Confirm → Post to Zoho
  2. Manual Entry → Post to Zoho

Run via:  python main.py
"""

import os
import sys
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.zoho_service import ZohoService
from app.services.groq_service import GroqService
from app.services.audio_service import AudioService
from app.config import settings

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Call Transcription Manager",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-title  { font-size: 2.5rem; color: #1f77b4; }
    .success-box { background-color: #d4edda; padding: 1rem; border-radius: 0.5rem; }
    .error-box   { background-color: #f8d7da; padding: 1rem; border-radius: 0.5rem; }
    .info-box    { background-color: #d1ecf1; padding: 1rem; border-radius: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================

for key, default in [
    ("current_tab",   "upload_transcribe"),
    ("transcription", ""),
    ("summary",       ""),
    ("call_id",       ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================================
# SIDEBAR — ZOHO TOKEN
# ============================================================================

with st.sidebar:
    st.markdown("## 🔑 Zoho Token")

    tokens = ZohoService.load_tokens()

    if tokens and "access_token" in tokens:
        st.success("✅ Token Saved")
        st.caption("Token is ready to use")
    else:
        st.warning("⚠️ No Token")
        st.caption("Generate token before posting to Zoho")

    auth_url = ZohoService.get_authorization_url()
    if auth_url:
        st.markdown(f"[🔑 Click to Generate Token]({auth_url})")
        st.caption("1. Click link → 2. Approve in Zoho → 3. Token saves automatically")

    st.divider()

    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key and len(groq_key) > 10:
        st.success("✅ Groq API")
    else:
        st.error("❌ Groq API key missing")

# ============================================================================
# HELPERS
# ============================================================================

def generate_summary(transcription: str) -> str:
    if not transcription or len(transcription.strip()) < 10:
        return "No valid transcription to summarize"
    with st.spinner("🤖 Generating summary..."):
        summary, success = GroqService.generate_summary(transcription, "manual")
    return summary if success else f"Error: {summary}"


def post_to_zoho(call_id: str, transcription: str, summary: str):
    try:
        with st.spinner("🔄 Refreshing token..."):
            ZohoService.refresh_access_token()
        with st.spinner("📤 Posting to Zoho..."):
            success, error = ZohoService.update_call(call_id, transcription, summary)
        return success, error
    except Exception as e:
        return False, f"Token error: {e}. Click 'Generate Token' in the sidebar."


def clear_session():
    st.session_state.transcription = ""
    st.session_state.summary       = ""
    st.session_state.call_id       = ""

# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="main-title">🎙️ Call Transcription Manager</div>
<p style="font-size:1.1rem; color:#666;">
    Upload audio or manually enter transcription, then post to Zoho CRM
</p>
""", unsafe_allow_html=True)

# ============================================================================
# TAB BUTTONS
# ============================================================================

col1, col2 = st.columns(2)

with col1:
    if st.button(
        "📥 Upload & Transcribe",
        use_container_width=True,
        key="btn_upload",
        type="primary" if st.session_state.current_tab == "upload_transcribe" else "secondary",
    ):
        st.session_state.current_tab = "upload_transcribe"
        st.rerun()

with col2:
    if st.button(
        "✏️ Manual Entry",
        use_container_width=True,
        key="btn_manual",
        type="primary" if st.session_state.current_tab == "manual_entry" else "secondary",
    ):
        st.session_state.current_tab = "manual_entry"
        st.rerun()

st.divider()

# ============================================================================
# TAB 1: UPLOAD & TRANSCRIBE
# ============================================================================

if st.session_state.current_tab == "upload_transcribe":
    st.subheader("📥 Option 1: Upload Audio & Transcribe")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Step 1: Call Information")
        call_id = st.text_input(
            "Call ID",
            value=st.session_state.call_id,
            help="Enter the Zoho CRM call ID",
        )
        st.session_state.call_id = call_id

    with col2:
        st.markdown("### Step 2: Audio URL")
        audio_url = st.text_input(
            "Audio URL",
            help="URL to download the audio file (m4a, mp3, wav)",
        )

    if st.button("⬇️ Download & Transcribe", use_container_width=True, key="btn_transcribe"):
        if not call_id or not audio_url:
            st.error("❌ Please provide both Call ID and Audio URL")
        else:
            try:
                with st.spinner("⬇️ Downloading audio..."):
                    audio_file, success, error = AudioService.download_audio(
                        audio_url, call_id, worker_id=1
                    )

                if not success:
                    st.error(f"❌ Download failed: {error}")
                else:
                    st.success("✅ Audio downloaded!")

                    with st.spinner("🎤 Transcribing..."):
                        transcript, status, _, _ = GroqService.transcribe_audio(
                            audio_file, call_id
                        )

                    AudioService.cleanup_audio(audio_file)

                    if status == "error":
                        st.error(f"❌ Transcription failed: {transcript}")
                    elif status == "no_speech":
                        st.warning("⚠️ No clear speech detected in audio")
                    else:
                        st.session_state.transcription = transcript
                        with st.spinner("🤖 Generating summary..."):
                            summary, _ = GroqService.generate_summary(transcript, call_id)
                        st.session_state.summary = summary
                        st.success("✅ Transcription complete!")
                        st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {e}")

    # Review & Edit (only shown after transcription)
    if st.session_state.transcription:
        st.divider()
        st.markdown("### Step 3: Review & Edit")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📝 Transcription")
            edited_transcript = st.text_area(
                "Transcription",
                value=st.session_state.transcription,
                height=200,
                label_visibility="collapsed",
            )
            st.session_state.transcription = edited_transcript

        with col2:
            st.markdown("#### 📋 Summary")
            edited_summary = st.text_area(
                "Summary",
                value=st.session_state.summary,
                height=200,
                label_visibility="collapsed",
            )
            st.session_state.summary = edited_summary

        st.divider()
        st.markdown("### Step 4: Confirm & Post")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ Confirm & Post to Zoho", use_container_width=True, key="btn_post_upload"):
                if not call_id or not st.session_state.transcription or not st.session_state.summary:
                    st.error("❌ Missing required information")
                else:
                    success, error = post_to_zoho(
                        call_id,
                        st.session_state.transcription,
                        st.session_state.summary,
                    )
                    if success:
                        st.success(f"✅ Posted to Zoho! (Call ID: {call_id})")
                        clear_session()
                        st.rerun()
                    else:
                        st.error(f"❌ Failed: {error}")

        with col2:
            if st.button("🔄 Regenerate Summary", use_container_width=True, key="btn_regen"):
                st.session_state.summary = generate_summary(st.session_state.transcription)
                st.rerun()

        with col3:
            if st.button("🗑️ Clear", use_container_width=True, key="btn_clear"):
                clear_session()
                st.rerun()

# ============================================================================
# TAB 2: MANUAL ENTRY
# ============================================================================

else:
    st.subheader("✏️ Option 2: Manual Entry")

    call_id_manual = st.text_input(
        "Call ID",
        value=st.session_state.call_id,
        help="Enter the Zoho CRM call ID",
    )
    st.session_state.call_id = call_id_manual

    st.markdown("### Transcription & Summary")

    col1, col2 = st.columns(2)

    with col1:
        transcription_manual = st.text_area(
            "Transcription",
            value=st.session_state.transcription,
            height=250,
            placeholder="Enter or paste the transcription here...",
        )
        st.session_state.transcription = transcription_manual

    with col2:
        summary_manual = st.text_area(
            "Summary",
            value=st.session_state.summary,
            height=250,
            placeholder="Enter or paste the summary here...",
        )
        st.session_state.summary = summary_manual

    st.divider()
    st.markdown("### Post to Zoho")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📤 Post to Zoho", use_container_width=True, key="btn_post_manual", type="primary"):
            if not call_id_manual or not st.session_state.transcription or not st.session_state.summary:
                st.error("❌ Please provide Call ID, Transcription, and Summary")
            else:
                success, error = post_to_zoho(
                    call_id_manual,
                    st.session_state.transcription,
                    st.session_state.summary,
                )
                if success:
                    st.success(f"✅ Posted to Zoho! (Call ID: {call_id_manual})")
                    st.balloons()
                    clear_session()
                    st.rerun()
                else:
                    st.error(f"❌ Failed: {error}")

    with col2:
        if st.button("🗑️ Clear", use_container_width=True, key="btn_clear_manual"):
            clear_session()
            st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<div style="text-align:center; color:#999; padding:1rem;">
    <p>🎙️ Call Transcription Manager v1.0</p>
    <p style="font-size:.9rem;">Powered by Groq Whisper &amp; Zoho CRM</p>
</div>
""", unsafe_allow_html=True)