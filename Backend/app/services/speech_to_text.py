import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings

logger = logging.getLogger(__name__)

class SpeechToTextService:
    def __init__(self):
        self.use_mock = settings.USE_MOCK_AI
        self.model = None
        
        if not self.use_mock:
            try:
                import whisper
                logger.info(f"Loading Whisper model '{settings.WHISPER_MODEL}'...")
                # Load Whisper model (CPU mode by default)
                self.model = whisper.load_model(settings.WHISPER_MODEL)
                logger.info("Whisper model loaded successfully.")
            except ImportError:
                logger.warning("openai-whisper library not found. Falling back to Mock Speech-To-Text.")
                self.use_mock = True
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}. Falling back to Mock Speech-To-Text.")
                self.use_mock = True

    async def transcribe(self, file_path: str) -> str:
        if self.use_mock:
            logger.info("Using Mock Speech-To-Text transcription.")
            return self._mock_transcribe(file_path)
        
        try:
            logger.info(f"Transcribing audio file: {file_path}")
            
            def _run():
                result = self.model.transcribe(file_path)
                return result.get("text", "").strip()

            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                text = await loop.run_in_executor(pool, _run)
            return text
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}. Falling back to mock transcript.")
            return self._mock_transcribe(file_path)

    def _mock_transcribe(self, file_path: str) -> str:
        filename = os.path.basename(file_path).lower()
        if "positive" in filename or "good" in filename or "happy" in filename or "resolved" in filename:
            return "Thank you so much. The payment was successful and the issue has finally been resolved. Your support team is amazing!"
        elif "negative" in filename or "angry" in filename or "bad" in filename or "fail" in filename or "frustrated" in filename:
            return "I have been waiting for my refund for three days and nobody has solved my problem. This is a billing issue and I want to cancel my subscription immediately."
        elif "refund" in filename:
            return "My refund hasn't arrived even though I requested it last week. Can you check my refund status?"
        elif "billing" in filename or "payment" in filename or "charge" in filename:
            return "I have a question about my monthly bill. I was charged twice for this month subscription."
        elif "technical" in filename or "login" in filename or "broken" in filename:
            return "I am unable to login to my account. The password reset page is broken and returns a 500 error."
        else:
            # Default neutral transcript
            return "Hello, I want to know the status of my service request. It was submitted yesterday."

stt_service = SpeechToTextService()
