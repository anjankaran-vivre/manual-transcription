# 🚀 Streamlit Setup Guide

Complete step-by-step guide to get the Call Transcription Manager running.

## Phase 1: Prerequisites

### Required Accounts
- ✅ Groq API account (free tier available)
- ✅ Zoho CRM account with admin access
- ✅ Python 3.8+

## Phase 2: Get Groq API Key

### Step 1: Create Groq Account
1. Go to https://console.groq.com
2. Sign up or log in
3. Navigate to "API Keys"
4. Create a new API key
5. Copy the key (you'll need it in `.env`)

**Keep your API key secure!** Don't share it or commit it to version control.

## Phase 3: Setup Zoho OAuth

### Step 1: Register OAuth App in Zoho

1. Log in to your Zoho CRM account
2. Go to **Settings** → **Setup** → **OAuth & Connected Apps**
3. Click **Create Application**
4. Fill in the form:
   - **Application Name**: Call Transcription Manager
   - **Client Type**: Web-based Application
   - **Homepage URL**: http://localhost:8501
   - **Authorized Redirect URI**: `http://localhost:8501`
   - **Description**: Call transcription and Zoho sync tool

5. Accept the terms and click **Create**

### Step 2: Get Credentials

After creating the app, you'll see:
- **Client ID**
- **Client Secret**

**Save these securely!** You'll need them in the next step.

### Step 3: Configure .env File

1. In the project root directory, copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in your credentials:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   
   ZOHO_CLIENT_ID=your_client_id
   ZOHO_CLIENT_SECRET=your_client_secret
   ZOHO_REDIRECT_URI=http://localhost:8501
   ```

3. Save the file

## Phase 4: Install Dependencies

```bash
# Install Streamlit and dependencies
pip install -r requirements_streamlit.txt
```

## Phase 5: First Run - Authorize with Zoho

### Step 1: Start the App

```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

### Step 2: Authorize with Zoho

1. You'll see a message in the sidebar about authorization
2. Click the authorization link
3. You'll be redirected to Zoho to approve access
4. Accept the permission request
5. Zoho will redirect back to `http://localhost:8501` with an authorization code in the URL
6. Extract the code from the URL (usually looks like: `code=abc123xyz...`)
7. Go back to the Streamlit app
8. Paste the authorization code in the input field
9. Click "Save Token"

### What Happens Next

Once authorized:
- Your tokens are saved locally in `zoho_tokens.json`
- The token will automatically refresh before each post
- You're ready to use the app!

## Phase 6: Verify Setup

### Checklist

- [ ] Python installed and working
- [ ] `.env` file created with all variables
- [ ] Streamlit installed (`pip show streamlit`)
- [ ] Request library installed (`pip show requests`)
- [ ] App starts without errors (`streamlit run streamlit_app.py`)
- [ ] Authorized with Zoho (saw the OAuth flow)
- [ ] Token saved (`zoho_tokens.json` exists)

### Quick Test

1. Run the app: `streamlit run streamlit_app.py`
2. Try **Option 2: Manual Entry**
3. Fill in:
   - Call ID: `1` (or any valid Call ID from Zoho)
   - Transcription: `Test transcription`
   - Summary: `Test summary`
4. Click "Post to Zoho"

If successful, you'll see: ✅ Successfully posted to Zoho!

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'streamlit'"
**Solution**: Install requirements
```bash
pip install -r requirements_streamlit.txt
```

### Issue: "GROQ_API_KEY not set in environment"
**Solution**: 
- Check `.env` file exists
- Verify GROQ_API_KEY is set
- Restart the app after updating `.env`

### Issue: "No tokens found" or "No refresh token found"
**Solution**:
- You haven't completed the Zoho OAuth flow yet
- Run the app and look for the authorization link in the sidebar
- Complete the OAuth flow
- Run the app again

### Issue: "Authorization failed" or "Invalid client_id"
**Solution**:
- Double-check your Zoho credentials in `.env`
- Make sure ZOHO_REDIRECT_URI matches exactly in Zoho settings
- Verify Client ID and Secret are correct

### Issue: "Download timeout"
**Solution**:
- The audio URL took too long to download (>120 seconds)
- Try with a different URL
- Check your internet connection

### Issue: "Transcription failed"
**Solution**:
- Verify GROQ_API_KEY is correct
- Try with a smaller audio file
- Check audio format is supported (mp3, m4a, wav)
- Check audio file isn't corrupted

### Issue: "Failed to post to Zoho: Status 500"
**Solution**:
- The Call ID might not exist in Zoho
- The custom fields (Transcription_c, Summary_c) might not exist
- Check your Zoho permissions
- Verify Call ID is correct

### Issue: "Permission denied: 'zoho_tokens.json'"
**Solution**:
- File permissions issue
- Try: `chmod 644 zoho_tokens.json`
- Or delete and re-authorize: `rm zoho_tokens.json`

## Advanced: Running Behind a Proxy

If you're behind a corporate proxy, set environment variables:

```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080
```

Then run the app.

## Production Deployment

### Not Recommended
This app is designed for **local/development use only**:
- Stores tokens on disk (security risk)
- Uses local temporary files
- Designed for single user

### For Production
- Use proper OAuth token storage (database with encryption)
- Deploy behind HTTPS
- Use environment variables for all secrets
- Add authentication (login required)
- Add audit logging
- Use cloud storage for temporary files

## Next Steps

1. ✅ Complete the setup above
2. ✅ Test with manual entry (Option 2)
3. ✅ Test with upload and transcribe (Option 1)
4. ✅ Verify posts appear in Zoho CRM
5. ✅ Customize as needed

## Getting Help

**For Groq Issues**:
- Docs: https://console.groq.com/docs
- Check your API quota: https://console.groq.com/playground

**For Zoho Issues**:
- Zoho Help: https://help.zoho.com
- Custom fields must exist in Zoho first

**For Streamlit Issues**:
- Docs: https://docs.streamlit.io
- GitHub: https://github.com/streamlit/streamlit

---

**Ready to go!** 🚀

Once you've completed this guide, you can start using the app immediately.
