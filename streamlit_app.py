"""
Streamlit Frontend for Call Transcription and Zoho Integration
Simple 2-option interface:
1. Download → Transcribe → Edit → Confirm → Post to Zoho
2. Manual Entry → Post to Zoho
"""

import streamlit as st
import os
import sys
import tempfile
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.zoho_service import ZohoService
from services.groq_service import GroqService
from services.audio_service import AudioService
from services.quality_checker import QualityChecker

# Streamlit page config
st.set_page_config(
    page_title="Call Transcription Manager",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-title { font-size: 2.5rem; color: #1f77b4; }
    .success-box { background-color: #d4edda; padding: 1rem; border-radius: 0.5rem; }
    .error-box { background-color: #f8d7da; padding: 1rem; border-radius: 0.5rem; }
    .info-box { background-color: #d1ecf1; padding: 1rem; border-radius: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "upload_transcribe"
if "transcription" not in st.session_state:
    st.session_state.transcription = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "call_id" not in st.session_state:
    st.session_state.call_id = ""

# ============================================================================
# SIDEBAR: STATUS & CONFIGURATION
# ============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    # Check Zoho Authorization Status
    tokens = ZohoService.load_tokens()
    if tokens and "access_token" in tokens:
        st.success("✅ Zoho Authorized")
    else:
        st.warning("⚠️ Zoho Authorization Required")
        st.markdown("""
        ### First-Time Setup Required!
        
        1. Get your authorization code:
           - Click the link below
           - Approve access in Zoho
           - You'll be redirected with a code in the URL
        
        2. Copy the authorization code
        3. Paste it below
        """)
        
        auth_url = ZohoService.get_authorization_url()
        if auth_url:
            st.markdown(f"[🔗 Click here to authorize](#) or visit:")
            st.code(auth_url, language="text")
            
            auth_code = st.text_input("Paste authorization code here:", type="password")
            if auth_code and auth_code.strip():
                if st.button("Save Token"):
                    tokens, error = ZohoService.generate_access_token(auth_code.strip())
                    if error:
                        st.error(f"Authorization failed: {error}")
                    else:
                        st.success("✅ Authorization successful! Reload the page.")
                        st.rerun()
        else:
            st.error("❌ Configuration error: Check ZOHO_CLIENT_ID in .env")
    
    st.divider()
    
    # Check API Configuration
    st.markdown("### API Status")
    
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and len(groq_key) > 10:
        st.success("✅ Groq API: Configured")
    else:
        st.error("❌ Groq API: Not configured (check .env)")
    
    st.divider()
    
    # Help & Documentation
    st.markdown("### 📚 Help & Documentation")
    st.markdown("""
    - [Setup Guide](SETUP_GUIDE.md)
    - [Full README](README_STREAMLIT.md)
    - [Groq Docs](https://console.groq.com/docs)
    - [Zoho Help](https://help.zoho.com)
    """)

def generate_summary(transcription):
    """Generate summary using Groq"""
    try:
        if not transcription or len(transcription.strip()) < 10:
            return "No valid transcription to summarize"
        
        with st.spinner("🤖 Generating summary..."):
            summary = GroqService.generate_summary(transcription)
            return summary
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def post_to_zoho(call_id, transcription, summary):
    """Post transcription and summary to Zoho"""
    try:
        with st.spinner("🔄 Refreshing Zoho token..."):
            ZohoService.refresh_access_token()
        
        with st.spinner("📤 Posting to Zoho..."):
            success, error = ZohoService.update_call(call_id, transcription, summary)
            return success, error
    except Exception as e:
        return False, str(e)

# ============================================================================
# HEADER
# ============================================================================
st.markdown("""
<div class="main-title">🎙️ Call Transcription Manager</div>
<p style="font-size: 1.1rem; color: #666;">Upload audio or manually edit transcription, then post to Zoho CRM</p>
""", unsafe_allow_html=True)

# ============================================================================
# TAB SELECTION
# ============================================================================
col1, col2 = st.columns(2)
with col1:
    if st.button("📥 Upload & Transcribe", use_container_width=True, 
                 key="btn_upload", 
                 type="primary" if st.session_state.current_tab == "upload_transcribe" else "secondary"):
        st.session_state.current_tab = "upload_transcribe"
        st.rerun()

with col2:
    if st.button("✏️ Manual Entry", use_container_width=True, 
                 key="btn_manual",
                 type="primary" if st.session_state.current_tab == "manual_entry" else "secondary"):
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
        st.markdown("### Step 1: Provide Call Information")
        call_id = st.text_input(
            "Call ID",
            value=st.session_state.call_id,
            help="Enter the Zoho CRM call ID"
        )
        st.session_state.call_id = call_id
    
    with col2:
        st.markdown("### Step 2: Download Audio")
        audio_url = st.text_input(
            "Audio URL",
            help="URL to download the audio file (m4a, mp3, wav)"
        )
    
    # Download and Transcribe button
    col1, col2 = st.columns([2, 1])
    with col1:
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
                        st.success("✅ Audio downloaded successfully!")
                        
                        # Transcribe
                        with st.spinner("🎤 Transcribing audio..."):
                            transcript, status, raw_transcript, api_calls = GroqService.transcribe_audio(
                                audio_file, call_id
                            )
                        
                        # Cleanup audio
                        AudioService.cleanup_audio(audio_file)
                        
                        if status == "error":
                            st.error(f"❌ Transcription failed: {transcript}")
                        elif status == "no_speech":
                            st.warning("⚠️ No clear speech detected in audio")
                        else:
                            st.session_state.transcription = transcript
                            
                            # Generate summary
                            with st.spinner("🤖 Generating summary..."):
                                summary = GroqService.generate_summary(transcript)
                            st.session_state.summary = summary
                            
                            st.success("✅ Transcription complete!")
                            st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Display and Edit Section
    if st.session_state.transcription:
        st.divider()
        st.markdown("### Step 3: Review & Edit")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📝 Transcription")
            transcription_edited = st.text_area(
                "Transcription (edit if needed)",
                value=st.session_state.transcription,
                height=200,
                label_visibility="collapsed"
            )
            st.session_state.transcription = transcription_edited
        
        with col2:
            st.markdown("#### 📋 Summary")
            summary_edited = st.text_area(
                "Summary (edit if needed)",
                value=st.session_state.summary,
                height=200,
                label_visibility="collapsed"
            )
            st.session_state.summary = summary_edited
        
        # Post to Zoho
        st.divider()
        st.markdown("### Step 4: Confirm & Post to Zoho")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Confirm & Post to Zoho", use_container_width=True, key="btn_post_upload"):
                if not call_id or not st.session_state.transcription or not st.session_state.summary:
                    st.error("❌ Missing required information")
                else:
                    success, error = post_to_zoho(
                        call_id,
                        st.session_state.transcription,
                        st.session_state.summary
                    )
                    
                    if success:
                        st.success(f"✅ Successfully posted to Zoho! (Call ID: {call_id})")
                        # Clear session
                        st.session_state.transcription = ""
                        st.session_state.summary = ""
                        st.session_state.call_id = ""
                    else:
                        st.error(f"❌ Failed to post to Zoho: {error}")
        
        with col2:
            if st.button("🔄 Regenerate Summary", use_container_width=True, key="btn_regen"):
                summary = generate_summary(st.session_state.transcription)
                st.session_state.summary = summary
                st.rerun()
        
        with col3:
            if st.button("🗑️ Clear", use_container_width=True, key="btn_clear"):
                st.session_state.transcription = ""
                st.session_state.summary = ""
                st.session_state.call_id = ""
                st.rerun()

# ============================================================================
# TAB 2: MANUAL ENTRY
# ============================================================================
else:
    st.subheader("✏️ Option 2: Manual Entry")
    
    col1, col2 = st.columns(2)
    
    with col1:
        call_id_manual = st.text_input(
            "Call ID",
            value=st.session_state.call_id,
            help="Enter the Zoho CRM call ID"
        )
        st.session_state.call_id = call_id_manual
    
    with col2:
        st.markdown("")
        st.markdown("")  # Spacing
    
    st.markdown("### Transcription & Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        transcription_manual = st.text_area(
            "Transcription",
            value=st.session_state.transcription,
            height=250,
            placeholder="Enter or paste the transcription here..."
        )
        st.session_state.transcription = transcription_manual
    
    with col2:
        summary_manual = st.text_area(
            "Summary",
            value=st.session_state.summary,
            height=250,
            placeholder="Enter or paste the summary here..."
        )
        st.session_state.summary = summary_manual
    
    # Post to Zoho
    st.divider()
    st.markdown("### Post to Zoho")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Post to Zoho", use_container_width=True, key="btn_post_manual", type="primary"):
            if not call_id_manual or not st.session_state.transcription or not st.session_state.summary:
                st.error("❌ Please provide Call ID, Transcription, and Summary")
            else:
                success, error = post_to_zoho(
                    call_id_manual,
                    st.session_state.transcription,
                    st.session_state.summary
                )
                
                if success:
                    st.success(f"✅ Successfully posted to Zoho! (Call ID: {call_id_manual})")
                    st.balloons()
                    # Clear session
                    st.session_state.transcription = ""
                    st.session_state.summary = ""
                    st.session_state.call_id = ""
                    st.rerun()
                else:
                    st.error(f"❌ Failed to post to Zoho: {error}")
    
    with col2:
        if st.button("🗑️ Clear", use_container_width=True, key="btn_clear_manual"):
            st.session_state.transcription = ""
            st.session_state.summary = ""
            st.session_state.call_id = ""
            st.rerun()

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #999; padding: 1rem;">
    <p>🎙️ Call Transcription Manager v1.0</p>
    <p style="font-size: 0.9rem;">Powered by Groq Whisper & Zoho CRM</p>
</div>
""", unsafe_allow_html=True)
