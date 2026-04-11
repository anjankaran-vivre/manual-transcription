import os
import json
import base64
import requests
from typing import Optional, Tuple
from app.config import settings


class OpenRouterService:
   

    MODEL = "google/gemini-2.5-flash-lite"
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    @staticmethod
    def _detect_audio_format(audio_bytes: bytes, file_ext: str = "mp3") -> str:
        """
        Detect audio format from magic bytes or extension.
        
        Returns format string for OpenRouter API
        """
        # Try magic bytes first
        if audio_bytes.startswith((b'\xff\xfb', b'\xff\xf3', b'ID3')):
            return "mp3"
        elif b'ftyp' in audio_bytes[:20]:
            return "mp4"
        elif audio_bytes.startswith(b'RIFF') and audio_bytes[8:12] == b'WAVE':
            return "wav"
        elif audio_bytes.startswith(b'OggS'):
            return "ogg"
        
        # Fallback to extension map
        format_map = {
            "mp3": "mp3",
            "wav": "wav",
            "webm": "webm",
            "ogg": "ogg",
            "flac": "flac",
            "m4a": "mp4",
        }
        return format_map.get(file_ext.lower(), "mp3")

    @staticmethod
    def _encode_audio_to_base64(audio_bytes: bytes) -> Optional[str]:
        """Encode audio bytes to base64."""
        try:
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            return audio_base64
        except Exception:
            return None

    @staticmethod
    def transcribe_audio(audio_file_path: str, call_id: str) -> Tuple[str, str, str, int]:
        """
        Transcribe audio using OpenRouter + Gemini.
        Returns: (transcript, status, raw_transcript, api_calls)
        """
        api_calls = 0

        try:
            with open(audio_file_path, "rb") as f:
                audio_bytes = f.read()

            if len(audio_bytes) < 500:
                return "", "no_speech", "", api_calls

            # Detect file type by magic bytes
            if audio_bytes.startswith((b'\xff\xfb', b'\xff\xf3', b'ID3')):
                file_ext = "mp3"
            elif b'ftyp' in audio_bytes[:20]:
                file_ext = "m4a"
            elif audio_bytes.startswith(b'RIFF') and audio_bytes[8:12] == b'WAVE':
                file_ext = "wav"
            else:
                file_ext = "mp3"

            audio_format = OpenRouterService._detect_audio_format(audio_bytes, file_ext)

            # Encode audio as base64
            audio_base64 = OpenRouterService._encode_audio_to_base64(audio_bytes)
            if not audio_base64:
                return "", "error", "", api_calls

            # System and user prompts for transcription
            system_prompt = """You are a professional call transcription specialist.
Your task is to accurately transcribe the call conversation.

STRICT RULES:
1. Capture the FULL conversation EXACTLY as spoken
2. Do NOT include speaker labels or identifiers
3. Translate to proper, formal English if needed
4. Do NOT omit or modify any part
5. Return ONLY the transcription text"""

            user_prompt = """Transcribe this call audio completely and accurately.
Return only the full transcription text without any speaker labels or markdown."""

            # Initialize headers for OpenRouter API
            if not settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY == "your_openrouter_api_key_here":
                print("[OpenRouter Transcription Error] OPENROUTER_API_KEY not set or invalid in .env\"")
                return "", "error", "", api_calls
                
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "Call Transcription Manager"
            }

            print(f"[OpenRouter Transcription] Starting transcription - Audio format: {audio_format}, Size: {len(audio_bytes)} bytes")

            # Create payload for transcription
            payload = {
                "model": OpenRouterService.MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": audio_base64,
                                    "format": audio_format
                                }
                            },
                            {"type": "text", "text": user_prompt}
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 4000
            }

            # Make direct HTTP request to OpenRouter
            response = requests.post(
                OpenRouterService.API_URL,
                json=payload,
                headers=headers,
                timeout=180
            )

            if response.status_code != 200:
                error_msg = f"OpenRouter API Error {response.status_code}: {response.text}"
                print(f"[OpenRouter Transcription Error] {error_msg}")
                return "", "error", "", api_calls

            result = response.json()
            raw_transcript = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            api_calls = 1

            if not raw_transcript:
                print("[OpenRouter Transcription] No speech detected in audio")
                return "", "no_speech", "", api_calls

            # Simple quality check
            word_count = len(raw_transcript.split())
            is_clear = word_count > 3
            
            if not is_clear:
                print(f"[OpenRouter Transcription] Unclear audio - only {word_count} words detected")
                return "", "unclear_audio", raw_transcript, api_calls

            print(f"[OpenRouter Transcription] Success - {word_count} words transcribed")
            return raw_transcript, "success", raw_transcript, api_calls

        except requests.exceptions.Timeout:
            print("[OpenRouter Transcription Error] Request timeout (180s exceeded)")
            return "", "error", "", api_calls
        except requests.exceptions.ConnectionError as e:
            print(f"[OpenRouter Transcription Error] Connection failed: {str(e)}")
            return "", "error", "", api_calls
        except Exception as e:
            print(f"[OpenRouter Transcription Error] {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return "", "error", "", api_calls

    @staticmethod
    def generate_summary(transcript: str, call_id: str) -> Tuple[str, bool]:
        """
        Generate PURPOSE & OUTCOME summary using Gemini.
        Returns: (summary, success)
        """
        try:
            if len(transcript) > 10000:
                transcript = transcript[:10000] + "... [truncated]"

            system_prompt = """You are a professional CRM call summarizer.
Summarize ONLY based on the transcript provided.
Create two concise sections: PURPOSE and OUTCOME.

RULES:
- Be specific. Include product/service names if mentioned.
- PURPOSE: Main issue, request, or discussion topic.
- OUTCOME: Decisions made, resolutions, or next actions.
- If unclear, say "Not clearly mentioned."
- Each section: 1-2 concise sentences.
- Return ONLY the formatted response with PURPOSE and OUTCOME"""

            user_prompt = f"""Summarize this call transcript:

Transcript:
{transcript}

Response format:
PURPOSE: ...
OUTCOME: ..."""

            # Initialize headers for OpenRouter API
            if not settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY == "your_openrouter_api_key_here":
                print("[OpenRouter Summary Error] OPENROUTER_API_KEY not set or invalid in .env")
                return "PURPOSE: Not available\nOUTCOME: See transcript", False
            
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "Call Transcription Manager"
            }

            print(f"[OpenRouter Summary] Starting summary generation for {len(transcript)} characters")

            # Create payload for summary
            payload = {
                "model": OpenRouterService.MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 500
            }

            # Make direct HTTP request to OpenRouter
            response = requests.post(
                OpenRouterService.API_URL,
                json=payload,
                headers=headers,
                timeout=60
            )

            if response.status_code != 200:
                error_msg = f"OpenRouter API Error {response.status_code}: {response.text}"
                print(f"[OpenRouter Summary Error] {error_msg}")
                return "PURPOSE: Not available\nOUTCOME: See transcript", False

            result = response.json()
            summary = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            if not summary:
                print("[OpenRouter Summary] No summary generated")
                return "PURPOSE: Not available\nOUTCOME: See transcript", False
            
            print(f"[OpenRouter Summary] Success - {len(summary)} characters generated")
            return summary, True

        except requests.exceptions.Timeout:
            print("[OpenRouter Summary Error] Request timeout (60s exceeded)")
            return "PURPOSE: Not available\nOUTCOME: See transcript", False
        except requests.exceptions.ConnectionError as e:
            print(f"[OpenRouter Summary Error] Connection failed: {str(e)}")
            return "PURPOSE: Not available\nOUTCOME: See transcript", False
        except Exception as e:
            print(f"[OpenRouter Summary Error] {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return "PURPOSE: Not available\nOUTCOME: See transcript", False
