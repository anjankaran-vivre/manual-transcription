# Streamlit Call Transcription Manager

A simplified, frontend-based application for transcribing call audio and posting results to Zoho CRM.

## 🎯 Key Features

### Option 1: Upload & Transcribe
- Input Call ID and Audio URL
- Automatically download audio
- Transcribe using Groq Whisper
- Auto-generate summary
- Review and edit in UI
- Post to Zoho CRM

### Option 2: Manual Entry
- Input Call ID directly
- Manually paste transcription and summary
- Post to Zoho CRM directly

## 🔑 Key Improvements

### Removed Components
- ❌ Database connections (no SQL, no ORM)
- ❌ FastAPI backend
- ❌ Socket.IO real-time updates
- ❌ Background task processing
- ❌ Email notifications
- ❌ Complex logging system
- ❌ PID file management
- ❌ Worker processes

### Simplified Components
- ✅ **Groq Service**: Direct HTTP calls only
- ✅ **Zoho Service**: Token refresh + direct HTTP updates
- ✅ **Audio Service**: Simple download with retry
- ✅ **Quality Checker**: Transcript cleaning utilities

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_streamlit.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

**Required Variables:**
- `GROQ_API_KEY` - Get from https://console.groq.com/keys
- `ZOHO_CLIENT_ID` - From Zoho CRM OAuth settings
- `ZOHO_CLIENT_SECRET` - From Zoho CRM OAuth settings
- `ZOHO_REDIRECT_URI` - Usually http://localhost:8501

### 3. Initial Zoho Authorization

Before first use, you need to authorize with Zoho:

1. Update `.env` with your Zoho OAuth credentials
2. Run the app and check the sidebar for authorization instructions
3. Visit the provided Zoho OAuth URL
4. Approve access and copy the authorization code
5. Paste the code in the app to save tokens

### 4. Run Streamlit App

```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## 📋 Detailed Usage

### Option 1: Upload & Transcribe Workflow

1. **Step 1**: Enter your Zoho Call ID
2. **Step 2**: Provide the audio URL (m4a, mp3, or wav)
3. **Step 3**: Click "Download & Transcribe"
   - Audio downloads to temporary directory
   - Transcribed using Groq Whisper
   - Summary auto-generated using Groq LLM
4. **Step 4**: Review and edit
   - Edit transcription as needed
   - Edit summary as needed
5. **Step 5**: Click "Confirm & Post to Zoho"
   - Token automatically refreshed before posting
   - Results saved to Zoho CRM

### Option 2: Manual Entry Workflow

1. Enter your Zoho Call ID
2. Paste or enter transcription
3. Paste or enter summary
4. Click "Post to Zoho"
   - Token automatically refreshed before posting
   - Results saved to Zoho CRM

## 🔐 Token Management

The app automatically handles Zoho OAuth tokens:

- **First time**: You'll authorize once and get a refresh token
- **Auto-refresh**: Before each post, the token is refreshed automatically
- **Token storage**: Tokens saved in `zoho_tokens.json` (keep secure!)

**Important**: The token refresh happens automatically when you click "Post", so you don't need to manual step.

## 📁 Project Structure

```
Manual_Transcription/
├── streamlit_app.py              # Main Streamlit application
├── requirements_streamlit.txt    # Streamlit dependencies
├── .env.example                  # Environment template
├── zoho_tokens.json             # Token storage (auto-generated)
└── services/
    ├── __init__.py
    ├── groq_service.py          # Transcription & Summary
    ├── zoho_service.py          # Zoho OAuth & CRM API
    ├── audio_service.py         # Audio download
    └── quality_checker.py       # Transcript cleaning
```

## 🔄 Workflow Diagram

### Option 1: Upload & Transcribe
```
User Input (ID + URL)
    ↓
Download Audio
    ↓
Transcribe (Groq Whisper)
    ↓
Generate Summary (Groq LLM)
    ↓
Display in UI for Editing
    ↓
User Reviews & Edits
    ↓
Refresh Zoho Token
    ↓
Post to Zoho CRM
    ↓
Success!
```

### Option 2: Manual Entry
```
User Input (ID + Text + Summary)
    ↓
Refresh Zoho Token
    ↓
Post to Zoho CRM
    ↓
Success!
```

## ⚙️ Groq Service

The Groq service uses the OpenAI-compatible API endpoints:

**Transcription**: `https://api.groq.com/openai/v1/audio/translations`
- Model: `whisper-large-v3`
- Supports: MP3, M4A, WAV, WebM

**Summary**: `https://api.groq.com/openai/v1/chat/completions`
- Model: `mixtral-8x7b-32768`
- Generates concise professional summaries

## 🔗 Zoho CRM Integration

The app updates Zoho Call records with two fields:
- `Transcription_c`: Full transcription (max 2000 chars)
- `Summary_c`: Call summary

**Required Scopes**:
- `CRM.modules.calls.UPDATE`
- `CRM.modules.calls.READ`

## 🛠️ Troubleshooting

### "No refresh token found"
- Run the app, click authorization link in sidebar
- Complete the Zoho OAuth flow
- Tokens will be saved for future use

### "GROQ_API_KEY not set"
- Check your `.env` file
- Verify API key from https://console.groq.com/keys
- Restart the app after updating `.env`

### "Download timeout"
- Check URL is accessible
- Try a different audio URL
- Ensure credentials are correct if authentication required

### "Transcription failed"
- Check audio file is valid
- Try a smaller audio file first
- Verify Groq API key is valid

## 📊 API Metrics

**Transcription Cost**: ~0.02 credits per minute of audio
**Summary Cost**: ~0.0001 credits per request

## 🔒 Security Notes

- Never commit `.env` or `zoho_tokens.json` to version control
- Add to `.gitignore`:
  ```
  .env
  zoho_tokens.json
  *.pyc
  __pycache__/
  .streamlit/
  ```
- Tokens are stored locally and never leave your machine
- Use HTTPS redirect URIs in production

## 📝 Supported Audio Formats

- MP3 (.mp3)
- M4A (.m4a)
- WAV (.wav)
- WebM (.webm)
- FLAC (.flac)

Maximum audio file: Groq accepts up to 25MB per request

## 🚨 Important Notes

1. **Token Refresh**: Before posting to Zoho, the app automatically refreshes the OAuth token. This is critical for the post to succeed.

2. **Audio Cleanup**: Downloaded audio files are automatically deleted after processing (uses temp directory).

3. **Transcription Limits**: 
   - Transcription truncated at 2000 chars when posting to Zoho
   - Quality checker removes excessive repetitions automatically

4. **Error Handling**: All errors are shown in the UI with detailed messages. Check the error message for troubleshooting.

## 📞 Support

For issues with:
- **Groq API**: https://console.groq.com
- **Zoho CRM**: https://help.zoho.com
- **Streamlit**: https://docs.streamlit.io

---

**Version**: 1.0.0
**Last Updated**: April 2026
