"""
Simplified Groq Service for Streamlit
- Direct HTTP calls to Groq API
- Transcription using Whisper
- Summary generation using LLM
"""

import os
import io
import requests
from dotenv import load_dotenv

load_dotenv()

class GroqService:
    """Streamlit-optimized Groq Service"""
    
    WHISPER_ENDPOINT = "https://api.groq.com/openai/v1/audio/translations"
    CHAT_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
    
    @staticmethod
    def get_api_key():
        """Get Groq API key from environment"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise Exception("GROQ_API_KEY not set in environment")
        return api_key
    
    @staticmethod
    def transcribe_audio(audio_file_path: str, call_id: str):
        """
        Transcribe audio using Groq Whisper
        Returns: (transcript, status, raw_transcript, api_calls)
        
        status: 'success', 'no_speech', 'error'
        """
        try:
            file_size = os.path.getsize(audio_file_path)
            
            if file_size < 500:
                return "", "no_speech", "", 0
            
            with open(audio_file_path, "rb") as f:
                audio_bytes = f.read()
            
            # Detect file type by magic bytes
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
                "model": "whisper-large-v3",
                "response_format": "verbose_json"
            }
            headers = {
                "Authorization": f"Bearer {GroqService.get_api_key()}"
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
                return "", "error", f"Whisper API error {response.status_code}: {error_text}", 0
            
            result = response.json()
            
            # Extract transcript
            raw_transcript = result.get("text", "").strip()
            if not raw_transcript and "segments" in result:
                raw_transcript = " ".join(
                    seg.get("text", "").strip()
                    for seg in result["segments"]
                    if seg.get("text")
                )
            
            if not raw_transcript:
                return "", "no_speech", "", 1
            
            # Clean transcript
            from services.quality_checker import QualityChecker
            transcript = QualityChecker.clean_transcript(raw_transcript)
            
            return transcript, "success", raw_transcript, 1
        
        except Exception as e:
            return "", "error", f"Transcription error: {str(e)}", 0
    
    @staticmethod
    def generate_summary(transcription: str, max_words: int = 100):
        """
        Generate a summary of the transcription using Groq LLM
        Returns: summary text
        """
        try:
            if not transcription or len(transcription.strip()) < 10:
                return "No valid transcription to summarize"
            
            headers = {
                "Authorization": f"Bearer {GroqService.get_api_key()}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional call summarizer. Create concise, professional summaries of call transcriptions."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this call transcript in {max_words} words or less:\n\n{transcription}"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 256
            }
            
            response = requests.post(
                GroqService.CHAT_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code != 200:
                error_text = response.text[:200]
                return f"Summary generation failed: {error_text}"
            
            result = response.json()
            summary = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return summary if summary else "Could not generate summary"
        
        except Exception as e:
            return f"Error generating summary: {str(e)}"
