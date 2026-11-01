import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings

logger = logging.getLogger(__name__)

class SentimentService:
    def __init__(self):
        self.use_mock = settings.USE_MOCK_AI
        self.pipeline = None
        
        if not self.use_mock:
            try:
                from transformers import pipeline
                logger.info(f"Loading sentiment model '{settings.SENTIMENT_MODEL}'...")
                self.pipeline = pipeline(
                    "sentiment-analysis",
                    model=settings.SENTIMENT_MODEL,
                    tokenizer=settings.SENTIMENT_MODEL
                )
                logger.info("Sentiment pipeline loaded successfully.")
            except ImportError:
                logger.warning("transformers library not found. Falling back to Mock Sentiment.")
                self.use_mock = True
            except Exception as e:
                logger.error(f"Error loading sentiment model: {e}. Falling back to Mock Sentiment.")
                self.use_mock = True

    async def analyze(self, text: str) -> dict:
        if not text or not text.strip():
            return {"label": "neutral", "confidence": 1.0}
            
        if self.use_mock:
            logger.info("Using Mock Sentiment Analysis.")
            return self._mock_analyze(text)
            
        try:
            logger.info(f"Analyzing sentiment of text: {text[:50]}...")
            
            def _run():
                results = self.pipeline(text)
                if results and len(results) > 0:
                    res = results[0]
                    # Map the label output to lowercase
                    label = res.get("label", "neutral").lower()
                    score = float(res.get("score", 0.5))
                    
                    # Distilbert student model outputs positive, neutral, negative
                    # In case of other model labels, normalize them
                    if label not in ["positive", "neutral", "negative"]:
                        if "pos" in label:
                            label = "positive"
                        elif "neg" in label:
                            label = "negative"
                        else:
                            label = "neutral"
                    
                    return {"label": label, "confidence": score}
                return {"label": "neutral", "confidence": 0.5}

            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(pool, _run)
            return result
        except Exception as e:
            logger.error(f"Transformers sentiment analysis failed: {e}. Falling back to mock analysis.")
            return self._mock_analyze(text)

    def _mock_analyze(self, text: str) -> dict:
        text_lower = text.lower()
        
        # Heuristic keywords mapping
        negative_words = ["cancel", "refund", "sue", "terrible", "bad", "angry", "frustrated", "broken", "worst", "waiting for three days", "disappointed", "nobody solved", "hate", "useless", "calling for three days"]
        positive_words = ["thank you", "thanks", "resolved", "great", "perfect", "amazing", "satisfied", "helpful", "good", "solved", "fixed"]
        
        neg_count = sum(1 for word in negative_words if word in text_lower)
        pos_count = sum(1 for word in positive_words if word in text_lower)
        
        if neg_count > pos_count:
            confidence = min(0.6 + (neg_count * 0.08), 0.98)
            return {"label": "negative", "confidence": confidence}
        elif pos_count > neg_count:
            confidence = min(0.6 + (pos_count * 0.08), 0.98)
            return {"label": "positive", "confidence": confidence}
        else:
            return {"label": "neutral", "confidence": 0.72}

sentiment_service = SentimentService()
