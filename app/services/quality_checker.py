import re
from collections import Counter
from app.logging.log_streamer import log_streamer

class QualityChecker:
    @staticmethod
    def check_audio_quality(transcript, call_id):
        """
        Check if transcript has clear speech or is low quality.
        Returns: (is_clear, reason)
        """
        if not transcript or len(transcript.strip()) == 0:
            return False, "empty_transcript"
        
        text = transcript.lower().strip()
        words = text.split()
        total_words = len(words)
        
        # Allow very short transcripts
        if total_words < 5:
            log_streamer.debug("QualityChecker", f"Call {call_id}: Short transcript ({total_words} words)")
            return True, "short_allowed"
        
        # Clean words
        cleaned_words = [re.sub(r'[.,!?"\']', '', w.lower()) for w in words]
        cleaned_words = [w for w in cleaned_words if w]
        
        if not cleaned_words:
            return False, "no_valid_words"
        
        word_counts = Counter(cleaned_words)
        most_common_word, most_common_count = word_counts.most_common(1)[0]
        frequency_ratio = most_common_count / len(cleaned_words)
        
        log_streamer.debug("QualityChecker", 
            f"Call {call_id}: Most common '{most_common_word}' = {frequency_ratio*100:.1f}%")
        
        # Single word 80%+ of transcript
        if frequency_ratio >= 0.80:
            return False, f"repetitive_{most_common_word}_{frequency_ratio*100:.0f}pct"
        
        # Top 2 words 90%+ with few unique words
        if len(word_counts) >= 2:
            top_two = word_counts.most_common(2)
            top_two_count = top_two[0][1] + top_two[1][1]
            top_two_ratio = top_two_count / len(cleaned_words)
            unique_words = len(word_counts)
            
            if top_two_ratio >= 0.90 and unique_words <= 4:
                return False, f"low_variety_{unique_words}_unique"
        
        # 10+ consecutive repetitions
        consecutive_count = 1
        max_consecutive = 1
        
        for i in range(1, len(cleaned_words)):
            if cleaned_words[i] == cleaned_words[i-1] and len(cleaned_words[i]) > 0:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 1
        
        if max_consecutive >= 10:
            return False, f"consecutive_repeat_{max_consecutive}"
        
        # Very low unique ratio for longer transcripts
        if total_words >= 20:
            unique_ratio = len(word_counts) / len(cleaned_words)
            if unique_ratio < 0.1:
                return False, f"low_unique_{unique_ratio*100:.0f}pct"
        
        return True, "clear_speech"
    
    @staticmethod
    def clean_transcript(transcript):
        """Remove excessive repetitions from transcript"""
        if not transcript:
            return transcript
        
        words = transcript.split()
        if len(words) < 2:
            return transcript
        
        cleaned = [words[0]]
        consecutive = 1
        
        for i in range(1, len(words)):
            current_clean = re.sub(r'[.,!?]', '', words[i].lower())
            prev_clean = re.sub(r'[.,!?]', '', words[i-1].lower())
            
            if current_clean == prev_clean:
                consecutive += 1
                if consecutive <= 4:
                    cleaned.append(words[i])
            else:
                consecutive = 1
                cleaned.append(words[i])
        
        return ' '.join(cleaned)