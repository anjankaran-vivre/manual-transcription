import os
import io
import requests
from app.config import settings
from app.services.quality_checker import QualityChecker


class GroqService:
    WHISPER_ENDPOINT = "https://api.groq.com/openai/v1/audio/translations"
    CHAT_ENDPOINT    = "https://api.groq.com/openai/v1/chat/completions"

    @staticmethod
    def transcribe_audio(audio_file_path: str, call_id: str):
        """
        Transcribe audio using Groq Whisper.
        Returns: (transcript, status, raw_transcript, api_calls)
        """
        api_calls = 0

        try:
            file_size = os.path.getsize(audio_file_path)

            if file_size < 500:
                return "", "no_speech", "", api_calls

            with open(audio_file_path, "rb") as f:
                audio_bytes = f.read()

            if audio_bytes.startswith((b'\xff\xfb', b'\xff\xf3', b'ID3')):
                file_ext = "mp3"
            elif b'ftyp' in audio_bytes[:20]:
                file_ext = "m4a"
            elif audio_bytes.startswith(b'RIFF') and audio_bytes[8:12] == b'WAVE':
                file_ext = "wav"
            else:
                file_ext = "mp3"

            files = {
                "file": (f"recording.{file_ext}", io.BytesIO(audio_bytes))
            }
            data = {
                "model":           "whisper-large-v3",
                "response_format": "verbose_json"
            }
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}"
            }

            response = requests.post(
                GroqService.WHISPER_ENDPOINT,
                files=files,
                data=data,
                headers=headers,
                timeout=180
            )

            if response.status_code != 200:
                error_text = response.text[:200]
                return "", "error", "", api_calls

            result    = response.json()
            api_calls = 1

            raw_transcript = result.get("text", "").strip()
            if not raw_transcript and "segments" in result:
                raw_transcript = " ".join(
                    seg.get("text", "").strip()
                    for seg in result["segments"]
                    if seg.get("text")
                )

            word_count = len(raw_transcript.split())

            if not raw_transcript:
                return "", "no_speech", "", api_calls

            is_clear, reason = QualityChecker.check_audio_quality(raw_transcript, call_id)
            if not is_clear:
                return "", "unclear_audio", raw_transcript, api_calls

            clean_transcript = QualityChecker.clean_transcript(raw_transcript)

            return clean_transcript, "success", raw_transcript, api_calls

        except Exception as e:
            return "", "error", "", api_calls

    @staticmethod
    def generate_summary(transcript: str, call_id: str):
        """
        Generate PURPOSE & OUTCOME summary.
        Returns: (summary, success)
        """
        try:
            if len(transcript) > 10000:
                transcript = transcript[:10000] + "... [truncated]"

            prompt = f"""You are a CRM call summarizer.
Summarize ONLY based on the transcript below — do not invent or assume any context.
Provide two concise sections: PURPOSE and OUTCOME.

Guidelines:
- Be specific. Include product/service names if mentioned.
- PURPOSE: Main issue, request, or discussion topic.
- OUTCOME: Decisions made, resolutions, or next actions.
- If unclear, say "Not clearly mentioned."
- Each section: 1–2 concise sentences.

Format:
PURPOSE: ...
OUTCOME: ...

Transcript:
{transcript}"""

            payload = {
                "model":       "llama-3.1-8b-instant",
                "messages":    [{"role": "user", "content": prompt}],
                "max_tokens":  300,
                "temperature": 0.4
            }
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type":  "application/json"
            }

            response = requests.post(
                GroqService.CHAT_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=60
            )

            if response.status_code != 200:
                return "PURPOSE: Failed to generate\nOUTCOME: See transcript", False

            summary = response.json()["choices"][0]["message"]["content"].strip()
            return summary, True

        except Exception as e:
            return "PURPOSE: Not available\nOUTCOME: See transcript", False