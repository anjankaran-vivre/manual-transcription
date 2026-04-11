"""
Streamlit Frontend for Call Transcription and Zoho Integration
"""

import os
import sys
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.zoho_service import ZohoService
from app.services.groq_service import GroqService
from app.services.openrouter_service import OpenRouterService
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
    ("audio_file",    None),
    ("transcription_method", "Whisper"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================================
# SIDEBAR
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
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    if openrouter_key and len(openrouter_key) > 10 and openrouter_key != "your_openrouter_api_key_here":
        st.success("✅ OpenRouter API")
    else:
        st.warning("⚠️ OpenRouter API (optional for Gemini)")

# ============================================================================
# HELPERS
# ============================================================================

def generate_summary(transcription: str) -> str:
    if not transcription or len(transcription.strip()) < 10:
        return "No valid transcription to summarize"
    with st.spinner("🤖 Generating summary..."):
        summary, success = GroqService.generate_summary(transcription, "manual")
    return summary if success else f"Error: {summary}"


def clear_session():
    # Clean up temp audio file
    if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
        AudioService.cleanup_audio(st.session_state.audio_file)
    st.session_state.transcription = ""
    st.session_state.summary       = ""
    st.session_state.call_id       = ""
    st.session_state.audio_file    = None
    st.session_state.transcription_method = "Whisper"

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
    
    st.markdown("### Step 3: Select Method")
    method = st.radio(
        "Choose transcription method:",
        options=["🎤 Whisper (Groq)", "🤖 Gemini (OpenRouter)"],
        index=0,
        horizontal=True,
        help="Whisper is faster (Groq API). Gemini uses OpenRouter."
    )
    st.session_state.transcription_method = "Whisper" if "Whisper" in method else "Gemini"

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
                    st.session_state.audio_file = audio_file

                    # Display audio player to verify quality
                    st.markdown("### 🔊 Listen to Audio")
                    st.divider()
                    try:
                        with open(audio_file, "rb") as f:
                            audio_data = f.read()
                        st.audio(audio_data, format="audio/mpeg")
                        st.caption("✓ Listen to verify audio quality before transcribing")
                    except Exception as e:
                        st.warning(f"Could not load audio player: {e}")
                    
                    st.divider()

                    with st.spinner(f"🎤 Transcribing with {st.session_state.transcription_method}..."):
                        if st.session_state.transcription_method == "Whisper":
                            transcript, status, _, _ = GroqService.transcribe_audio(
                                audio_file, call_id
                            )
                        else:  # Gemini
                            transcript, status, _, _ = OpenRouterService.transcribe_audio(
                                audio_file, call_id
                            )

                    if status == "error":
                        st.error(f"❌ Transcription failed: {transcript}")
                    elif status == "no_speech":
                        st.warning("⚠️ No clear speech detected in audio")
                    elif status == "unclear_audio":
                        st.warning("⚠️ Audio quality too low to transcribe clearly")
                    else:
                        st.session_state.transcription = transcript
                        with st.spinner(f"🤖 Generating summary with {st.session_state.transcription_method}..."):
                            if st.session_state.transcription_method == "Whisper":
                                summary, _ = GroqService.generate_summary(transcript, call_id)
                            else:  # Gemini
                                summary, _ = OpenRouterService.generate_summary(transcript, call_id)
                        st.session_state.summary = summary
                        st.success("✅ Transcription complete!")
                        st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {e}")

    # Review & Edit — only shown after transcription
    if st.session_state.transcription:
        st.divider()
        st.markdown("### Step 3: Review & Edit")

        # Audio player in review section
        if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
            with st.expander("🔊 Play Audio Again", expanded=False):
                try:
                    with open(st.session_state.audio_file, "rb") as f:
                        audio_data = f.read()
                    st.audio(audio_data, format="audio/mpeg")
                except Exception as e:
                    st.warning(f"Could not load audio: {e}")
        
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

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("✅ Confirm & Post to Zoho", use_container_width=True, key="btn_post_upload"):
                if not call_id:
                    st.error("❌ Please provide Call ID")
                elif not st.session_state.transcription.strip() and not st.session_state.summary.strip():
                    st.error("❌ Please provide at least Transcription or Summary")
                else:
                    with st.spinner("📤 Posting to Zoho..."):
                        try:
                            ZohoService.refresh_access_token()
                            success, error = ZohoService.update_call(
                                call_id,
                                st.session_state.transcription,
                                st.session_state.summary,
                            )
                        except Exception as e:
                            success = False
                            error = str(e)

                    if success:
                        st.success(f"✅ Posted to Zoho successfully! (Call ID: {call_id})")
                        if st.session_state.transcription.strip():
                            st.info(f"📝 Transcription: {st.session_state.transcription[:100]}...")
                        if st.session_state.summary.strip():
                            st.info(f"📋 Summary: {st.session_state.summary[:100]}...")
                        clear_session()
                    else:
                        st.error(f"❌ Failed to post to Zoho: {error}")

        with col2:
            # Re-transcribe with opposite method
            other_method = "Gemini" if st.session_state.transcription_method == "Whisper" else "Whisper"
            if st.button(f"🔄 Try {other_method}", use_container_width=True, key="btn_retranscribe"):
                if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
                    try:
                        st.session_state.transcription_method = other_method
                        with st.spinner(f"🎤 Transcribing with {other_method}..."):
                            if other_method == "Whisper":
                                transcript, status, _, _ = GroqService.transcribe_audio(
                                    st.session_state.audio_file, call_id
                                )
                            else:  # Gemini
                                transcript, status, _, _ = OpenRouterService.transcribe_audio(
                                    st.session_state.audio_file, call_id
                                )
                        
                        if status == "success":
                            st.session_state.transcription = transcript
                            # Generate summary with new method
                            with st.spinner(f"🤖 Generating summary with {other_method}..."):
                                if other_method == "Whisper":
                                    summary, _ = GroqService.generate_summary(transcript, call_id)
                                else:
                                    summary, _ = OpenRouterService.generate_summary(transcript, call_id)
                            st.session_state.summary = summary
                            st.success(f"✅ Re-transcribed with {other_method}!")
                            st.rerun()
                        else:
                            st.error(f"❌ Re-transcription failed")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.error("❌ Audio file not available")

        with col3:
            if st.button("🔄 Regenerate Summary", use_container_width=True, key="btn_regen"):
                if not st.session_state.transcription:
                    st.error("❌ No transcription to summarize")
                else:
                    with st.spinner("🤖 Generating summary..."):
                        summary, _ = GroqService.generate_summary(st.session_state.transcription, "manual")
                    st.session_state.summary = summary
                    st.rerun()

        with col4:
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
        st.markdown("#### 📝 Transcription")
        transcription_manual = st.text_area(
            "Transcription",
            value=st.session_state.transcription,
            height=250,
            placeholder="Enter or paste the transcription here...",
            label_visibility="collapsed",
        )
        st.session_state.transcription = transcription_manual

    with col2:
        st.markdown("#### 📋 Summary")
        summary_manual = st.text_area(
            "Summary",
            value=st.session_state.summary,
            height=250,
            placeholder="Enter or paste the summary here...",
            label_visibility="collapsed",
        )
        st.session_state.summary = summary_manual

    st.divider()
    st.markdown("### Post to Zoho")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📤 Post to Zoho", use_container_width=True, key="btn_post_manual", type="primary"):
            if not call_id_manual:
                st.error("❌ Please provide Call ID")
            elif not st.session_state.transcription.strip() and not st.session_state.summary.strip():
                st.error("❌ Please provide at least Transcription or Summary")
            else:
                with st.spinner("📤 Posting to Zoho..."):
                    try:
                        ZohoService.refresh_access_token()
                        success, error = ZohoService.update_call(
                            call_id_manual,
                            st.session_state.transcription,
                            st.session_state.summary,
                        )
                    except Exception as e:
                        success = False
                        error = str(e)

                if success:
                    st.success(f"✅ Posted to Zoho successfully! (Call ID: {call_id_manual})")
                    if st.session_state.transcription.strip():
                        st.info(f"📝 Transcription: {st.session_state.transcription[:100]}...")
                    if st.session_state.summary.strip():
                        st.info(f"📋 Summary: {st.session_state.summary[:100]}...")
                    st.balloons()
                    clear_session()
                else:
                    st.error(f"❌ Failed to post to Zoho: {error}")

    with col2:
        if st.button("🔄 Generate Summary", use_container_width=True, key="btn_gen_summary_manual"):
            if not st.session_state.transcription:
                st.error("❌ Enter transcription first")
            else:
                st.session_state.summary = generate_summary(st.session_state.transcription)
                st.rerun()

    with col3:
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