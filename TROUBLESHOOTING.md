# 🔧 Troubleshooting Guide

## Common Issues & Solutions

---

## Installation & Setup Issues

### Issue 1: "No module named 'streamlit'"

**Error Message**:
```
ModuleNotFoundError: No module named 'streamlit'
```

**Solution**:
```bash
# Install requirements
pip install -r requirements_streamlit.txt

# Or install individually
pip install streamlit requests python-dotenv
```

**Why it happens**: Dependencies not installed yet.

---

### Issue 2: ".env file not found"

**Error Message**:
```
Error: GROQ_API_KEY not set in environment
```

**Solution**:
```bash
# Copy template
cp .env.example .env

# Edit .env and add your credentials
# Then restart the app
```

**Why it happens**: Missing/not configured environment file.

---

### Issue 3: "Python version error"

**Error Message**:
```
Python 3.8+ required (you have 3.6)
```

**Solution**:
1. Install Python 3.8+
2. Use `python3` instead of `python`
3. Check version: `python --version`

**Why it happens**: Old Python version.

---

## Zoho OAuth & Token Issues

### Issue 4: "No refresh token found"

**Error Message**:
```
No refresh token found. Please authorize first.
```

**Solution**:
1. Run the app: `streamlit run streamlit_app.py`
2. Look in the sidebar for the authorization link
3. Click the link or copy-paste the URL
4. Complete the Zoho OAuth flow
5. Copy the authorization code from the redirect URL
6. Paste code in the app
7. Click "Save Token"

**Why it happens**: First-time setup requires authorization.

**Detailed Steps**:
```
1. Visit: https://accounts.zoho.in/oauth/v2/auth?...
2. Click "Accept"
3. You'll see: http://localhost:8501?code=ABC123...
4. Copy ABC123...
5. Paste in Streamlit app
6. Click "Save Token"
```

---

### Issue 5: "Authorization failed: Invalid client_id"

**Error Message**:
```
The client_id provided is invalid. Ensure the client id is valid
```

**Solution**:
1. Check `.env` file has correct `ZOHO_CLIENT_ID`
2. Verify in Zoho: Settings → OAuth → Copy Client ID
3. Make sure no extra spaces in `.env`
4. Restart the app after updating

**Why it happens**: Wrong credentials or spaces in `.env`.

---

### Issue 6: "redirect_uri_mismatch"

**Error Message**:
```
The redirect_uri provided doesn't match what is registered
```

**Solution**:
1. In `.env`: `ZOHO_REDIRECT_URI=http://localhost:8501`
2. In Zoho settings: Register same URL
3. They must match exactly
4. Restart app

**Why it happens**: Redirect URI mismatch between app and Zoho settings.

---

### Issue 7: "Status 401: Unauthorized"

**Error Message**:
```
Status 401: Unauthorized when posting to Zoho
```

**Solution**:
1. Delete `zoho_tokens.json`
2. Re-authorize the app (go through OAuth flow again)
3. Tokens have likely expired

**Why it happens**: Token invalid or expired.

---

## API & Credential Issues

### Issue 8: "GROQ_API_KEY not valid"

**Error Message**:
```
401 Unauthorized from Groq API
```

**Solution**:
1. Get new API key: https://console.groq.com/keys
2. Update `.env` with new key
3. Restart the app
4. Test with a small audio file first

**Why it happens**: Invalid or revoked API key.

**Check your key**:
```bash
curl -H "Authorization: Bearer YOUR_KEY" \
     https://api.groq.com/openai/v1/models
```

---

### Issue 9: "Groq rate limit exceeded"

**Error Message**:
```
429 Too Many Requests
```

**Solution**:
1. Wait a few minutes
2. Free tier has limits
3. Consider upgrading Groq plan
4. Spread requests over time

**Why it happens**: Hit Groq API rate limit.

**Current free limits**:
- 30 requests per minute
- 600 requests per day

---

## Audio Download Issues

### Issue 10: "Download timeout"

**Error Message**:
```
Download timeout after 120 seconds
```

**Solution**:
1. Check URL is accessible
2. Try a different URL
3. Check internet connection
4. Audio might be on slow server

**Why it happens**: URL took too long to download.

---

### Issue 11: "Authentication failed for audio"

**Error Message**:
```
403 Forbidden when downloading audio
```

**Solution**:
1. Check if URL needs credentials
2. If yes, add to `.env`:
   ```
   AUDIO_USERNAME=your_username
   AUDIO_PASSWORD=your_password
   ```
3. Restart the app
4. Try again

**Why it happens**: Audio URL requires authentication.

---

### Issue 12: "Downloaded file too small"

**Error Message**:
```
Downloaded file too small (100 bytes)
```

**Solution**:
1. URL might be returning error page
2. Check URL is direct audio file
3. Try downloading in browser to test
4. Verify URL is correct

**Why it happens**: URL didn't return actual audio file.

---

## Transcription Issues

### Issue 13: "Transcription failed: Error 500"

**Error Message**:
```
500 Internal Server Error from Groq
```

**Solution**:
1. Try again (might be temporary)
2. Try with smaller audio file
3. Check audio format is supported
4. Check Groq API status

**Why it happens**: Groq API error or audio issue.

**Supported formats**: MP3, M4A, WAV, WebM, FLAC
**Max size**: 25MB

---

### Issue 14: "No clear speech detected"

**Error Message**:
```
No clear speech detected in audio
```

**Solution**:
1. Audio is too quiet or noisy
2. No actual speech in audio
3. Check audio file directly
4. Try with a clearer recording

**Why it happens**: Audio quality too low.

---

### Issue 15: "Excessive repetition detected"

**Status**: `Warning` (not an error)

**Solution**:
1. This is normal for very repetitive audio
2. One word repeated 80%+ of the time
3. You can still use the transcription
4. Edit manually if needed

**Why it happens**: Quality checker flagged low-quality transcription.

---

## Post to Zoho Issues

### Issue 16: "Status 400: Invalid field"

**Error Message**:
```
Status 400: The field Transcription_c is invalid
```

**Solution**:
1. Custom fields might not exist in Zoho
2. Check field names in Zoho: Settings → Customization → Calls
3. Fields must be: `Transcription_c` and `Summary_c`
4. If different, app needs code change

**Why it happens**: Custom fields don't exist or are named differently.

**To create custom fields**:
1. Zoho CRM → Settings → Customization → Calls
2. Add custom fields:
   - Label: Transcription
   - Field Name: Transcription_c (auto-generated)
   - Type: Large Text
3. Add Summary field similarly

---

### Issue 17: "Status 404: Call not found"

**Error Message**:
```
Status 404: Call record not found
```

**Solution**:
1. Call ID doesn't exist in Zoho
2. Verify Call ID is correct
3. Check Call ID in Zoho CRM
4. Try a valid Call ID

**Why it happens**: Invalid Call ID provided.

---

### Issue 18: "Status 403: Permission denied"

**Error Message**:
```
Status 403: You don't have permission to update calls
```

**Solution**:
1. OAuth token doesn't have update permission
2. Re-authorize with correct scopes
3. Delete `zoho_tokens.json`
4. Go through auth flow again
5. Check Zoho user has "Update" permission on Calls

**Why it happens**: Insufficient permissions.

---

### Issue 19: "Status 500 when posting"

**Error Message**:
```
Status 500: Internal Server Error
```

**Solution**:
1. Try again (might be temporary)
2. Check transcription length (max 2000 chars)
3. Check special characters in text
4. Check Zoho token is valid

**Why it happens**: Zoho API error or data issue.

---

## UI & Performance Issues

### Issue 20: "App runs slowly"

**Slow Transcription**:
- Normal for long audio (30 sec per minute)
- Use shorter audio files
- Wait for it to complete

**Slow Download**:
- Check internet speed
- Try reducing audio file size
- Try different URL

**Slow Posting**:
- Normal (1-2 seconds)
- Check internet connection

---

### Issue 21: "Session state lost"

**Problem**: 
- Refreshing page loses data
- Back button doesn't work

**Solution**:
- This is normal Streamlit behavior
- Re-enter data before rerun
- Use browser back is not recommended
- Just refresh and start again

**Why it happens**: Streamlit resets on page refresh.

---

### Issue 22: "Text not appearing"

**Problem**:
- Transcription not showing
- Text area empty

**Solution**:
1. Wait for transcription to finish
2. Check console for errors
3. Try again with different audio
4. Refresh page and try again

**Why it happens**: Transcription failed silently.

---

## File & Permission Issues

### Issue 23: "Permission denied: 'zoho_tokens.json'"

**Error Message**:
```
PermissionError: [Errno 13] Permission denied: 'zoho_tokens.json'
```

**Solution**:
1. Change file permissions:
   ```bash
   chmod 644 zoho_tokens.json
   ```
2. Or delete and re-authorize:
   ```bash
   rm zoho_tokens.json
   ```
3. Then re-run app and authorize again

**Why it happens**: File permission issue.

---

### Issue 24: "Cannot create zoho_tokens.json"

**Error Message**:
```
PermissionError: Cannot write to zoho_tokens.json
```

**Solution**:
1. Check directory permissions
2. Try running from different directory
3. Or move project to home directory
4. Run: `chmod 755 /path/to/project`

**Why it happens**: Directory permission issue.

---

## Network & Connectivity

### Issue 25: "Connection refused"

**Error Message**:
```
ConnectionError: Connection refused
```

**Solution**:
1. Check internet connection
2. Check VPN if using one
3. Check firewall settings
4. Verify DNS resolution

**Test internet**:
```bash
ping google.com
```

**Why it happens**: Network connectivity issue.

---

## Quick Diagnosis

### "It's not working" - Try This:

1. **Restart app**:
   ```bash
   # Stop Ctrl+C
   # Run again
   streamlit run streamlit_app.py
   ```

2. **Check logs**:
   - Look at terminal output
   - Look at Streamlit UI messages
   - Look at error boxes in red

3. **Check credentials**:
   ```bash
   # Verify .env
   cat .env
   ```

4. **Check internet**:
   ```bash
   ping google.com
   ```

5. **Try quickstart**:
   ```bash
   python quickstart.py
   ```

---

## Getting Help

### Where to Find Help

| Issue | Resource |
|-------|----------|
| Groq Errors | https://console.groq.com/docs |
| Zoho Errors | https://help.zoho.com |
| Streamlit Help | https://docs.streamlit.io |
| Python Issues | https://docs.python.org |

### How to Report Issues

Include:
1. Error message (exact copy)
2. What you were trying to do
3. Steps to reproduce
4. Output of `python quickstart.py`

---

## Did This Help?

- ✅ **Yes**: Great! You're all set
- ❌ **No**: Check the documentation files:
  - `SETUP_GUIDE.md` - Setup instructions
  - `README_STREAMLIT.md` - Features & usage
  - `REFACTOR_SUMMARY.md` - Architecture overview

---

**Version**: 1.0.0
**Last Updated**: April 2026

