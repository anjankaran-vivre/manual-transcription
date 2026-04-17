"""
Streamlit Frontend — Call Transcription Manager
Tabs:
  Admin  → Upload & Transcribe | Manual Entry | File Upload Transcription
  User   → File Upload Transcription only
"""

import os
import sys
import streamlit as st
from dotenv import load_dotenv
from credential.auth import USERS_FILE

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.zoho_service import ZohoService
from app.services.groq_service import GroqService
from app.services.openrouter_service import OpenRouterService
from app.services.audio_service import AudioService
from app.services.file_transcription_service import FileTranscriptionService
from credential.auth import authenticate, is_admin
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
    .main-title      { font-size: 2.2rem; font-weight: 700; color: #1f77b4; }
    .sub-title       { font-size: 1.1rem; color: #888; margin-bottom: 1rem; }

    /* Role badges — always white text */
    .role-badge-admin { background:#1f77b4; color:white !important; padding:2px 10px;
                        border-radius:12px; font-size:.8rem; }
    .role-badge-user  { background:#4caf50; color:white !important; padding:2px 10px;
                        border-radius:12px; font-size:.8rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INIT
# ============================================================================

_defaults = {
    # auth
    "logged_in":              False,
    "current_user":           None,
    # shared
    "current_tab":            "upload_transcribe",
    "transcription":          "",
    "summary":                "",
    "call_id":                "",
    "audio_file":             None,
    "transcription_method":   "Whisper",
    # file transcription tab
    "ft_transcript":          "",
    "ft_summary":             "",
    "ft_metadata":            {},
    "ft_filename":            "",
}

for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================================
# ── LOGIN PAGE ──────────────────────────────────────────────────────────────
# ============================================================================

# print("Looking for users.json at:", USERS_FILE)
# print("File exists:", os.path.exists(USERS_FILE))

def render_login():
    st.markdown("""
    <div style='text-align:center; padding: 2rem 0 1rem'>
        <div class='main-title'>🎙️ Call Transcription Manager</div>
        <div class='sub-title'>Please sign in to continue</div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.2, 1])

    with col_c:
        with st.container(border=True):
            st.markdown("### 🔐 Sign In")
            st.write("")

            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )
            st.write("")

            if st.button("Sign In", use_container_width=True, type="primary"):
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    success, user = authenticate(username, password)
                    if success:
                        st.session_state.logged_in    = True
                        st.session_state.current_user = user
                        # Set default tab based on role
                        if is_admin(user):
                            st.session_state.current_tab = "upload_transcribe"
                        else:
                            st.session_state.current_tab = "file_transcription"
                        st.success(f"Welcome, {user['display_name']}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")

            st.divider()
            st.caption("Contact your administrator if you need access.")


# ============================================================================
# ── HELPERS ─────────────────────────────────────────────────────────────────
# ============================================================================

def clear_session():
    """Reset all working state (keep login)."""
    if st.session_state.audio_file and os.path.exists(st.session_state.audio_file or ""):
        AudioService.cleanup_audio(st.session_state.audio_file)

    reset_keys = {
        "transcription": "", "summary": "", "call_id": "",
        "audio_file": None, "transcription_method": "Whisper",
        "ft_transcript": "", "ft_summary": "", "ft_metadata": {},
        "ft_filename": "",
    }
    for k, v in reset_keys.items():
        st.session_state[k] = v


def clear_ft_session():
    """Reset only file-transcription state."""
    st.session_state.ft_transcript = ""
    st.session_state.ft_summary    = ""
    st.session_state.ft_metadata   = {}
    st.session_state.ft_filename   = ""


def render_speaker_transcript(transcript: str):
    """Render colour-coded speaker blocks — visible in BOTH light and dark themes."""
    import re

    colours = [
        "#4da6ff",  # bright blue
        "#ff9f43",  # bright orange
        "#2ed573",  # bright green
        "#ff6b6b",  # bright red
        "#c56cf0",  # bright purple
        "#f8a5c2",  # bright pink
        "#7bed9f",  # mint green
        "#70a1ff",  # light blue
    ]

    lines = transcript.strip().split("\n")
    current_speaker = None
    current_text    = []
    blocks          = []

    speaker_pattern = re.compile(r"^(Speaker\s*\d+)\s*:", re.IGNORECASE)

    for line in lines:
        m = speaker_pattern.match(line.strip())
        if m:
            if current_speaker is not None:
                blocks.append((current_speaker, " ".join(current_text).strip()))
            current_speaker = m.group(1).strip()
            rest = line[m.end():].strip()
            current_text = [rest] if rest else []
        else:
            if line.strip():
                current_text.append(line.strip())

    if current_speaker is not None:
        blocks.append((current_speaker, " ".join(current_text).strip()))

    if not blocks:
        st.text_area(
            "Transcript",
            value=transcript,
            height=300,
            label_visibility="collapsed",
        )
        return

    # Build speaker → colour map
    all_speakers = list(dict.fromkeys(b[0] for b in blocks))
    sp_colour = {sp: colours[i % len(colours)] for i, sp in enumerate(all_speakers)}

    for speaker, text in blocks:
        colour = sp_colour[speaker]
        st.markdown(
            f"""<div style='
                    border-left: 4px solid {colour};
                    padding: 0.6rem 1rem;
                    margin: 0.35rem 0;
                    border-radius: 0 6px 6px 0;
                    font-size: 0.95rem;
                '>
                <b style='color: {colour};'>{speaker}</b><br>
                <span style='color: inherit;'>{text}</span>
            </div>""",
            unsafe_allow_html=True,
        )

def render_summary_sections(summary: str):
    """Render structured summary — visible in both light and dark themes."""
    section_icons = {
        "CALL OVERVIEW":  "📞",
        "PURPOSE":        "🎯",
        "KEY POINTS":     "📌",
        "OUTCOME":        "✅",
        "ACTION ITEMS":   "📋",
        "SENTIMENT":      "💬",
    }

    import re
    parts = re.split(
        r"(CALL OVERVIEW:|PURPOSE:|KEY POINTS:|OUTCOME:|ACTION ITEMS:|SENTIMENT:)",
        summary,
    )

    if len(parts) <= 1:
        st.markdown(summary)
        return

    i = 1
    while i < len(parts):
        header_raw = parts[i].rstrip(":")
        body       = parts[i + 1].strip() if i + 1 < len(parts) else ""
        icon       = section_icons.get(header_raw, "•")

        body_html = body.replace("\n", "<br>")

        st.markdown(
            f"""<div style='
                    border: 1px solid rgba(128, 128, 128, 0.3);
                    border-radius: 8px;
                    padding: 1rem 1.2rem;
                    margin: 0.5rem 0;
                '>
                <b style='color: inherit; font-size: 1rem;'>
                    {icon} {header_raw}
                </b><br>
                <span style='color: inherit; font-size: 0.95rem;'>
                    {body_html}
                </span>
            </div>""",
            unsafe_allow_html=True,
        )
        i += 2


# ============================================================================
# ── SIDEBAR (only when logged in) ──────────────────────────────────────────
# ============================================================================

def render_sidebar():
    user = st.session_state.current_user

    with st.sidebar:
        # ── User info ── #
        role_class = "role-badge-admin" if is_admin(user) else "role-badge-user"
        role_label = "Admin" if is_admin(user) else "User"
        st.markdown(
            f"**{user['display_name']}** "
            f"<span class='{role_class}'>{role_label}</span>",
            unsafe_allow_html=True,
        )

        if st.button("🚪 Sign Out", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        st.divider()

        # ── Zoho (admin only) ── #
        if is_admin(user):
            st.markdown("## 🔑 Zoho Token")
            tokens = ZohoService.load_tokens()
            if tokens and "access_token" in tokens:
                st.success("✅ Token Saved")
                st.caption("Token ready to use")
            else:
                st.warning("⚠️ No Token")
                st.caption("Generate before posting to Zoho")

            auth_url = ZohoService.get_authorization_url()
            if auth_url:
                st.markdown(f"[🔑 Generate Token]({auth_url})")
                st.caption("Click → Approve in Zoho → Auto-saved")

            st.divider()

        # ── API status ── #
        st.markdown("### API Status")

        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key and len(groq_key) > 10:
            st.success("✅ Groq API")
        else:
            st.error("❌ Groq API key missing")

        or_key = os.getenv("OPENROUTER_API_KEY", "")
        if or_key and len(or_key) > 10 and or_key != "your_openrouter_api_key_here":
            st.success("✅ OpenRouter API")
        else:
            st.warning("⚠️ OpenRouter API not set")


# ============================================================================
# ── TAB: FILE UPLOAD TRANSCRIPTION ─────────────────────────────────────────
# ============================================================================

def render_file_transcription_tab():
    st.subheader("📂 File Upload Transcription")
    st.caption(
        "Upload any audio file for AI-powered transcription with "
        "speaker diarization and detailed summary."
    )

    supported = FileTranscriptionService.get_supported_extensions()

    # ── Upload area ── #
    col_upload, col_options = st.columns([2, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=supported,
            help=f"Supported formats: {', '.join(supported).upper()}",
            key="ft_file_uploader",
        )

    with col_options:
        st.markdown("#### ⚙️ Options")
        num_speakers = st.selectbox(
            "Number of speakers",
            options=["Auto-detect", "1", "2", "3", "4", "5", "6"],
            index=0,
            help="Specify if you know the number of speakers",
        )
        speaker_hint = None if num_speakers == "Auto-detect" else int(num_speakers)

        language_note = st.checkbox(
            "Translate to English",
            value=True,
            help="Non-English audio will be translated",
        )

    # ── Audio preview ── #
    if uploaded_file:
        st.markdown("#### 🔊 Audio Preview")
        st.audio(uploaded_file, format=f"audio/{uploaded_file.name.split('.')[-1]}")
        st.caption(
            f"📁 **{uploaded_file.name}** — "
            f"{round(uploaded_file.size / 1024, 1)} KB"
        )

        st.divider()

        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            transcribe_btn = st.button(
                "🎤 Transcribe Now",
                use_container_width=True,
                type="primary",
                key="ft_transcribe_btn",
            )

        if transcribe_btn:
            audio_bytes = uploaded_file.read()

            or_key = os.getenv("OPENROUTER_API_KEY", "")
            if not or_key or or_key == "your_openrouter_api_key_here":
                st.error(
                    "❌ OpenRouter API key is not configured. "
                    "Add OPENROUTER_API_KEY to your .env file."
                )
            else:
                with st.spinner(
                    f"🎤 Transcribing **{uploaded_file.name}** "
                    f"({'auto-detecting speakers' if not speaker_hint else f'{speaker_hint} speaker(s)'})…"
                ):
                    transcript, status, metadata = (
                        FileTranscriptionService.transcribe_with_speakers(
                            audio_bytes,
                            uploaded_file.name,
                            num_speakers=speaker_hint,
                        )
                    )

                if status == "error":
                    st.error(f"❌ Transcription failed: {metadata.get('error', 'Unknown error')}")

                elif status == "no_speech":
                    st.warning("⚠️ No speech detected in the audio file.")
                    st.info(
                        "Tips:\n"
                        "- Check that the file contains audio\n"
                        "- Ensure the file is not corrupted\n"
                        "- Try a different format"
                    )

                elif status == "unclear_audio":
                    st.warning("⚠️ Audio quality too low — limited text extracted.")
                    if transcript:
                        st.text_area("Partial transcript", transcript, height=100)

                else:
                    # ── Success ── #
                    st.session_state.ft_transcript = transcript
                    st.session_state.ft_filename   = uploaded_file.name
                    st.session_state.ft_metadata   = metadata

                    # Auto-generate summary
                    with st.spinner("🤖 Generating detailed summary…"):
                        summary, _ = FileTranscriptionService.generate_detailed_summary(
                            transcript
                        )
                    st.session_state.ft_summary = summary

                    st.success(
                        f"✅ Transcription complete — "
                        f"**{metadata.get('word_count', 0)}** words, "
                        f"**{metadata.get('speaker_count', 1)}** speaker(s) detected"
                    )
                    st.rerun()

    # ── Results (shown after transcription) ── #
    if st.session_state.ft_transcript:
        st.divider()
        st.markdown(f"### 📄 Results — *{st.session_state.ft_filename}*")

        # Metadata pills
        m = st.session_state.ft_metadata
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Format",   m.get("format", "—").upper())
        c2.metric("Size",     f"{m.get('size_kb', 0)} KB")
        c3.metric("Words",    m.get("word_count", 0))
        c4.metric("Speakers", m.get("speaker_count", 1))

        st.divider()

        # ── Transcription view / edit ── #
        tab_view, tab_edit = st.tabs(["👁️ View (Speaker Colour)", "✏️ Edit Raw Text"])

        with tab_view:
            render_speaker_transcript(st.session_state.ft_transcript)

        with tab_edit:
            edited = st.text_area(
                "Edit transcription",
                value=st.session_state.ft_transcript,
                height=300,
                label_visibility="collapsed",
                key="ft_edit_area",
            )
            if edited != st.session_state.ft_transcript:
                st.session_state.ft_transcript = edited

        st.divider()

        # ── Summary ── #
        st.markdown("### 📋 AI Summary")

        tab_pretty, tab_raw = st.tabs(["✨ Formatted", "📝 Raw Text"])

        with tab_pretty:
            render_summary_sections(st.session_state.ft_summary)

        with tab_raw:
            edited_summary = st.text_area(
                "Edit summary",
                value=st.session_state.ft_summary,
                height=250,
                label_visibility="collapsed",
                key="ft_summary_edit",
            )
            if edited_summary != st.session_state.ft_summary:
                st.session_state.ft_summary = edited_summary

        st.divider()

        # ── Action buttons ── #
        col_a, col_b, col_c, col_d = st.columns(4)

        with col_a:
            if st.button("🔄 Regenerate Summary", use_container_width=True, key="ft_regen"):
                with st.spinner("🤖 Regenerating summary…"):
                    new_sum, _ = FileTranscriptionService.generate_detailed_summary(
                        st.session_state.ft_transcript
                    )
                st.session_state.ft_summary = new_sum
                st.rerun()

        with col_b:
            # Download transcript
            transcript_bytes = st.session_state.ft_transcript.encode("utf-8")
            fname = os.path.splitext(st.session_state.ft_filename)[0]
            st.download_button(
                "⬇️ Download Transcript",
                data=transcript_bytes,
                file_name=f"{fname}_transcript.txt",
                mime="text/plain",
                use_container_width=True,
                key="ft_dl_transcript",
            )

        with col_c:
            # Download summary
            summary_bytes = st.session_state.ft_summary.encode("utf-8")
            st.download_button(
                "⬇️ Download Summary",
                data=summary_bytes,
                file_name=f"{fname}_summary.txt",
                mime="text/plain",
                use_container_width=True,
                key="ft_dl_summary",
            )

        with col_d:
            if st.button("🗑️ Clear Results", use_container_width=True, key="ft_clear"):
                clear_ft_session()
                st.rerun()


# ============================================================================
# ── TAB: UPLOAD & TRANSCRIBE (Admin only) ───────────────────────────────────
# ============================================================================

def render_upload_transcribe_tab():
    st.subheader("📥 Upload & Transcribe (CRM Call)")

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
    )
    st.session_state.transcription_method = (
        "Whisper" if "Whisper" in method else "Gemini"
    )

    if st.button("⬇️ Download & Transcribe", use_container_width=True, key="btn_transcribe"):
        if not call_id or not audio_url:
            st.error("❌ Please provide both Call ID and Audio URL")
        else:
            try:
                with st.spinner("⬇️ Downloading audio…"):
                    audio_file, success, error = AudioService.download_audio(
                        audio_url, call_id, worker_id=1
                    )

                if not success:
                    st.error(f"❌ Download failed: {error}")
                else:
                    st.success("✅ Audio downloaded!")
                    st.session_state.audio_file = audio_file

                    st.markdown("### 🔊 Listen to Audio")
                    try:
                        with open(audio_file, "rb") as f:
                            audio_data = f.read()
                        st.audio(audio_data, format="audio/mpeg")
                    except Exception as e:
                        st.warning(f"Could not load audio player: {e}")

                    st.divider()

                    with st.spinner(
                        f"🎤 Transcribing with "
                        f"{st.session_state.transcription_method}…"
                    ):
                        if st.session_state.transcription_method == "Whisper":
                            transcript, status, _, _ = GroqService.transcribe_audio(
                                audio_file, call_id
                            )
                        else:
                            transcript, status, _, _ = OpenRouterService.transcribe_audio(
                                audio_file, call_id
                            )

                    if status == "error":
                        st.error("❌ Transcription failed")
                    elif status == "no_speech":
                        st.warning("⚠️ No clear speech detected")
                    elif status == "unclear_audio":
                        st.warning("⚠️ Audio quality too low")
                    else:
                        st.session_state.transcription = transcript
                        with st.spinner("🤖 Generating summary…"):
                            if st.session_state.transcription_method == "Whisper":
                                summary, _ = GroqService.generate_summary(
                                    transcript, call_id
                                )
                            else:
                                summary, _ = OpenRouterService.generate_summary(
                                    transcript, call_id
                                )
                        st.session_state.summary = summary
                        st.success("✅ Transcription complete!")
                        st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {e}")

    # ── Review & Edit ── #
    if st.session_state.transcription:
        st.divider()
        st.markdown("### Step 4: Review & Edit")

        if st.session_state.audio_file and os.path.exists(
            st.session_state.audio_file or ""
        ):
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
            edited = st.text_area(
                "Transcription",
                value=st.session_state.transcription,
                height=200,
                label_visibility="collapsed",
            )
            st.session_state.transcription = edited

        with col2:
            st.markdown("#### 📋 Summary")
            edited_sum = st.text_area(
                "Summary",
                value=st.session_state.summary,
                height=200,
                label_visibility="collapsed",
            )
            st.session_state.summary = edited_sum

        st.divider()
        st.markdown("### Step 5: Confirm & Post")
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if st.button("✅ Post to Zoho", use_container_width=True, key="btn_post_upload"):
                if not call_id:
                    st.error("❌ Provide Call ID")
                elif not st.session_state.transcription.strip() and not st.session_state.summary.strip():
                    st.error("❌ Provide transcription or summary")
                else:
                    with st.spinner("📤 Posting to Zoho…"):
                        try:
                            ZohoService.refresh_access_token()
                            success, error = ZohoService.update_call(
                                call_id,
                                st.session_state.transcription,
                                st.session_state.summary,
                            )
                        except Exception as e:
                            success, error = False, str(e)

                    if success:
                        st.success(f"✅ Posted! (Call ID: {call_id})")
                        clear_session()
                    else:
                        st.error(f"❌ Failed: {error}")

        with c2:
            other = "Gemini" if st.session_state.transcription_method == "Whisper" else "Whisper"
            if st.button(f"🔄 Try {other}", use_container_width=True, key="btn_retry"):
                if st.session_state.audio_file and os.path.exists(
                    st.session_state.audio_file or ""
                ):
                    with st.spinner(f"Transcribing with {other}…"):
                        if other == "Whisper":
                            t, s, _, _ = GroqService.transcribe_audio(
                                st.session_state.audio_file, call_id
                            )
                        else:
                            t, s, _, _ = OpenRouterService.transcribe_audio(
                                st.session_state.audio_file, call_id
                            )
                    if s == "success":
                        st.session_state.transcription        = t
                        st.session_state.transcription_method = other
                        with st.spinner("🤖 Generating summary…"):
                            if other == "Whisper":
                                sm, _ = GroqService.generate_summary(t, call_id)
                            else:
                                sm, _ = OpenRouterService.generate_summary(t, call_id)
                        st.session_state.summary = sm
                        st.rerun()
                    else:
                        st.error("❌ Re-transcription failed")

        with c3:
            if st.button("🔄 Regen Summary", use_container_width=True, key="btn_regen"):
                with st.spinner("🤖 Generating summary…"):
                    sm, _ = GroqService.generate_summary(
                        st.session_state.transcription, "manual"
                    )
                st.session_state.summary = sm
                st.rerun()

        with c4:
            if st.button("🗑️ Clear", use_container_width=True, key="btn_clear"):
                clear_session()
                st.rerun()


# ============================================================================
# ── TAB: MANUAL ENTRY (Admin only) ─────────────────────────────────────────
# ============================================================================

def render_manual_entry_tab():
    st.subheader("✏️ Manual Entry")

    call_id = st.text_input(
        "Call ID",
        value=st.session_state.call_id,
        help="Zoho CRM call ID",
    )
    st.session_state.call_id = call_id

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📝 Transcription")
        t = st.text_area(
            "Transcription",
            value=st.session_state.transcription,
            height=250,
            placeholder="Enter or paste the transcription here…",
            label_visibility="collapsed",
        )
        st.session_state.transcription = t

    with col2:
        st.markdown("#### 📋 Summary")
        s = st.text_area(
            "Summary",
            value=st.session_state.summary,
            height=250,
            placeholder="Enter or paste the summary here…",
            label_visibility="collapsed",
        )
        st.session_state.summary = s

    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("📤 Post to Zoho", use_container_width=True, type="primary", key="btn_post_manual"):
            if not call_id:
                st.error("❌ Provide Call ID")
            elif not st.session_state.transcription.strip() and not st.session_state.summary.strip():
                st.error("❌ Provide transcription or summary")
            else:
                with st.spinner("📤 Posting…"):
                    try:
                        ZohoService.refresh_access_token()
                        success, error = ZohoService.update_call(
                            call_id,
                            st.session_state.transcription,
                            st.session_state.summary,
                        )
                    except Exception as e:
                        success, error = False, str(e)

                if success:
                    st.success(f"✅ Posted! (Call ID: {call_id})")
                    st.balloons()
                    clear_session()
                else:
                    st.error(f"❌ Failed: {error}")

    with c2:
        if st.button("🔄 Generate Summary", use_container_width=True, key="btn_gen_manual"):
            if not st.session_state.transcription:
                st.error("❌ Enter transcription first")
            else:
                with st.spinner("🤖 Generating…"):
                    sm, _ = GroqService.generate_summary(
                        st.session_state.transcription, "manual"
                    )
                st.session_state.summary = sm
                st.rerun()

    with c3:
        if st.button("🗑️ Clear", use_container_width=True, key="btn_clear_manual"):
            clear_session()
            st.rerun()


# ============================================================================
# ── MAIN ROUTER ─────────────────────────────────────────────────────────────
# ============================================================================

def main():
    # ── Not logged in → show login ── #
    if not st.session_state.logged_in:
        render_login()
        return

    user     = st.session_state.current_user
    is_admin_user = is_admin(user)

    render_sidebar()

    # ── Header ── #
    st.markdown(
        f"""<div class='main-title'>🎙️ Call Transcription Manager</div>
        <div class='sub-title'>
            Welcome, <b>{user['display_name']}</b> — 
            {'Full access (Admin)' if is_admin_user else 'File transcription access'}
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Tab navigation ── #
    if is_admin_user:
        # Admin sees 3 tabs
        col1, col2, col3 = st.columns(3)

        tab_map = {
            "upload_transcribe": ("📥 Upload & Transcribe", col1),
            "manual_entry":      ("✏️ Manual Entry",        col2),
            "file_transcription":("📂 File Transcription",  col3),
        }

        for tab_key, (label, col) in tab_map.items():
            with col:
                btn_type = (
                    "primary"
                    if st.session_state.current_tab == tab_key
                    else "secondary"
                )
                if st.button(label, use_container_width=True, type=btn_type, key=f"tab_{tab_key}"):
                    st.session_state.current_tab = tab_key
                    st.rerun()

    else:
        # Regular users only see file transcription
        st.session_state.current_tab = "file_transcription"

    st.divider()

    # ── Render active tab ── #
    if st.session_state.current_tab == "file_transcription":
        render_file_transcription_tab()
    elif is_admin_user:
        if st.session_state.current_tab == "upload_transcribe":
            render_upload_transcribe_tab()
        elif st.session_state.current_tab == "manual_entry":
            render_manual_entry_tab()
    else:
        # Safety — non-admin trying to access admin tab
        st.session_state.current_tab = "file_transcription"
        render_file_transcription_tab()

    # ── Footer ── #
    st.divider()
    st.markdown(
        """<div style='text-align:center;color:#999;padding:1rem;'>
            <p>🎙️ Call Transcription Manager v2.0</p>
            <p style='font-size:.85rem;'>
                Powered by Groq Whisper · Gemini via OpenRouter · Zoho CRM
            </p>
        </div>""",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()