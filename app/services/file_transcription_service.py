"""
File Transcription Service using OpenRouter + Gemini
Supports: speaker diarization, multiple audio formats, detailed summaries
"""

import os
import base64
import requests
import json
from typing import Optional, Tuple, Dict, List
from app.config import settings


class FileTranscriptionService:
    """
    Handles file upload transcription with speaker diarization
    using OpenRouter + Gemini Flash
    """

    MODEL = "google/gemini-2.5-flash-lite"
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    # Supported formats and their MIME types
    SUPPORTED_FORMATS = {
        "mp3":  "audio/mpeg",
        "wav":  "audio/wav",
        "m4a":  "audio/mp4",
        "mp4":  "audio/mp4",
        "ogg":  "audio/ogg",
        "flac": "audio/flac",
        "webm": "audio/webm",
        "aac":  "audio/aac",
        "wma":  "audio/x-ms-wma",
        "opus": "audio/opus",
        "aiff": "audio/aiff",
        "amr":  "audio/amr",
    }

    @staticmethod
    def _get_headers() -> Optional[Dict]:
        """Build API headers. Returns None if API key missing."""
        key = settings.OPENROUTER_API_KEY
        if not key or key == "your_openrouter_api_key_here":
            return None
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Call Transcription Manager",
        }

    @staticmethod
    def _detect_format(audio_bytes: bytes, filename: str) -> Tuple[str, str]:
        """
        Detect audio format from magic bytes and filename extension.
        Returns: (format_key, mime_type)
        """
        # Magic byte detection
        magic_map = [
            (b'\xff\xfb',          "mp3"),
            (b'\xff\xf3',          "mp3"),
            (b'\xff\xf2',          "mp3"),
            (b'ID3',               "mp3"),
            (b'fLaC',              "flac"),
            (b'OggS',              "ogg"),
            (b'RIFF',              "wav"),
        ]

        for magic, fmt in magic_map:
            if audio_bytes.startswith(magic):
                if fmt == "wav":
                    # Double-check WAVE marker
                    if audio_bytes[8:12] == b'WAVE':
                        return fmt, FileTranscriptionService.SUPPORTED_FORMATS[fmt]
                else:
                    return fmt, FileTranscriptionService.SUPPORTED_FORMATS[fmt]

        # Check for ftyp (MP4/M4A) anywhere in first 20 bytes
        if b'ftyp' in audio_bytes[:20]:
            return "m4a", FileTranscriptionService.SUPPORTED_FORMATS["m4a"]

        # Fallback to file extension
        ext = os.path.splitext(filename)[1].lstrip(".").lower()
        if ext in FileTranscriptionService.SUPPORTED_FORMATS:
            return ext, FileTranscriptionService.SUPPORTED_FORMATS[ext]

        # Default fallback
        return "mp3", FileTranscriptionService.SUPPORTED_FORMATS["mp3"]

    @staticmethod
    def _encode_audio(audio_bytes: bytes) -> Optional[str]:
        """Base64-encode audio bytes."""
        try:
            return base64.b64encode(audio_bytes).decode("utf-8")
        except Exception:
            return None

    @staticmethod
    def _call_api(payload: Dict, timeout: int = 300) -> Tuple[Optional[str], Optional[str]]:
        """
        Make a call to OpenRouter API.
        Returns: (content, error_message)
        """
        headers = FileTranscriptionService._get_headers()
        if not headers:
            return None, "OPENROUTER_API_KEY not configured"

        try:
            response = requests.post(
                FileTranscriptionService.API_URL,
                json=payload,
                headers=headers,
                timeout=timeout,
            )

            if response.status_code != 200:
                return None, f"API Error {response.status_code}: {response.text[:300]}"

            result = response.json()
            content = (
                result.get("choices", [{}])[0]
                      .get("message", {})
                      .get("content", "")
                      .strip()
            )
            return content if content else None, None

        except requests.exceptions.Timeout:
            return None, f"Request timed out after {timeout}s"
        except requests.exceptions.ConnectionError as e:
            return None, f"Connection failed: {str(e)}"
        except Exception as e:
            return None, f"{type(e).__name__}: {str(e)}"

    # ------------------------------------------------------------------ #
    #  PUBLIC METHODS
    # ------------------------------------------------------------------ #

    @staticmethod
    def transcribe_with_speakers(
        audio_bytes: bytes,
        filename: str,
        num_speakers: Optional[int] = None,
    ) -> Tuple[str, str, Dict]:
        """
        Transcribe audio with speaker diarization.

        Args:
            audio_bytes : raw audio data
            filename    : original filename (used for format detection)
            num_speakers: hint for number of speakers (None = auto-detect)

        Returns:
            (transcript_with_labels, status, metadata)
            status: "success" | "no_speech" | "unclear_audio" | "error"
            metadata: dict with keys → format, size_kb, word_count, speaker_count, error
        """
        metadata: Dict = {
            "format": "unknown",
            "size_kb": round(len(audio_bytes) / 1024, 1),
            "word_count": 0,
            "speaker_count": 0,
            "error": None,
        }

        # ── Minimum size guard ────────────────────────────────────────── #
        if len(audio_bytes) < 500:
            metadata["error"] = "Audio file too small (< 500 bytes)"
            return "", "no_speech", metadata

        # ── Format detection ──────────────────────────────────────────── #
        fmt, _mime = FileTranscriptionService._detect_format(audio_bytes, filename)
        metadata["format"] = fmt
        print(f"[FileTranscription] Detected format: {fmt}, Size: {metadata['size_kb']} KB")

        # ── Base64 encode ─────────────────────────────────────────────── #
        audio_b64 = FileTranscriptionService._encode_audio(audio_bytes)
        if not audio_b64:
            metadata["error"] = "Failed to encode audio"
            return "", "error", metadata

        # ── Build speaker hint ────────────────────────────────────────── #
        if num_speakers:
            speaker_hint = (
                f"There are exactly {num_speakers} speakers in this audio. "
                f"Label them as Speaker 1, Speaker 2, … Speaker {num_speakers}."
            )
        else:
            speaker_hint = (
                "Auto-detect the number of speakers. "
                "Label each distinct voice as Speaker 1, Speaker 2, etc."
            )

        # ── Prompts ───────────────────────────────────────────────────── #
        system_prompt = """You are an expert audio transcription specialist with advanced speaker diarization capabilities.

Your task:
1. Transcribe the COMPLETE audio conversation with 100% accuracy
2. Identify and label each distinct speaker
3. Format output with clear speaker labels

FORMATTING RULES:
- Use format: "Speaker N: [spoken text]"
- Start a new line for each speaker change
- Keep consecutive speech from same speaker on same block
- Do NOT skip or summarize any spoken content
- Translate non-English speech to English if needed
- Include filler words (um, uh, etc.) for accuracy
- If only one speaker, label as "Speaker 1:"

OUTPUT: Return ONLY the labelled transcription. No headers, no explanations."""

        user_prompt = f"""{speaker_hint}

Transcribe this audio completely with speaker labels.
Format each line as: Speaker N: [text]
Return only the transcription."""

        payload = {
            "model": FileTranscriptionService.MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_b64,
                                "format": fmt,
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ],
            "temperature": 0.1,
            "max_tokens": 8000,
        }

        print("[FileTranscription] Sending transcription request to OpenRouter...")
        content, error = FileTranscriptionService._call_api(payload, timeout=300)

        if error:
            metadata["error"] = error
            print(f"[FileTranscription Error] {error}")
            return "", "error", metadata

        if not content:
            print("[FileTranscription] No speech detected")
            return "", "no_speech", metadata

        # ── Quality checks ────────────────────────────────────────────── #
        word_count = len(content.split())
        metadata["word_count"] = word_count

        if word_count < 3:
            print(f"[FileTranscription] Unclear audio — only {word_count} words")
            return content, "unclear_audio", metadata

        # ── Count speakers ────────────────────────────────────────────── #
        speaker_count = FileTranscriptionService._count_speakers(content)
        metadata["speaker_count"] = speaker_count

        print(
            f"[FileTranscription] Success — {word_count} words, "
            f"{speaker_count} speaker(s) detected"
        )
        return content, "success", metadata

    @staticmethod
    def _count_speakers(transcript: str) -> int:
        """Count unique speaker labels in transcript."""
        import re
        speakers = set(re.findall(r"Speaker\s+(\d+)\s*:", transcript, re.IGNORECASE))
        return len(speakers) if speakers else 1

    @staticmethod
    def generate_detailed_summary(transcript: str) -> Tuple[str, bool]:
        """
        Generate a detailed summary with multiple sections.

        Returns: (summary_text, success)
        """
        if not transcript or len(transcript.strip()) < 20:
            return _default_summary(), False

        # Truncate safely
        if len(transcript) > 12000:
            transcript = transcript[:12000] + "\n... [transcript truncated]"

        system_prompt = """You are a professional call analyst and summarizer.
Analyze the provided call transcript and produce a structured, insightful summary.

Be specific — mention names, products, amounts, dates if present.
If information is not available, write "Not mentioned."

Always return the summary in EXACTLY this format (keep the section headers):

CALL OVERVIEW:
[1-2 sentences describing what the call was about]

PURPOSE:
[Why the call was made / main topic discussed]

KEY POINTS:
• [Point 1]
• [Point 2]
• [Point 3 — add more if needed]

OUTCOME:
[What was decided, resolved, or agreed upon]

ACTION ITEMS:
• [Action 1 — who does what by when]
• [Action 2]
(Write "None identified" if no action items)

SENTIMENT:
[Overall tone: Positive / Neutral / Negative — and brief reason]"""

        user_prompt = f"""Analyze and summarize this call transcript:

---
{transcript}
---

Return the structured summary following the exact format specified."""

        payload = {
            "model": FileTranscriptionService.MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 1000,
        }

        print("[FileTranscription] Generating detailed summary...")
        content, error = FileTranscriptionService._call_api(payload, timeout=60)

        if error or not content:
            print(f"[FileTranscription Summary Error] {error}")
            return _default_summary(), False

        print(f"[FileTranscription] Summary generated — {len(content)} chars")
        return content, True

    @staticmethod
    def get_supported_extensions() -> List[str]:
        """Return list of supported file extensions for st.file_uploader."""
        return list(FileTranscriptionService.SUPPORTED_FORMATS.keys())


# ── Module-level helper ──────────────────────────────────────────────────── #

def _default_summary() -> str:
    return (
        "CALL OVERVIEW:\nNot available\n\n"
        "PURPOSE:\nNot available\n\n"
        "KEY POINTS:\n• Not available\n\n"
        "OUTCOME:\nNot available\n\n"
        "ACTION ITEMS:\nNone identified\n\n"
        "SENTIMENT:\nNot available"
    )