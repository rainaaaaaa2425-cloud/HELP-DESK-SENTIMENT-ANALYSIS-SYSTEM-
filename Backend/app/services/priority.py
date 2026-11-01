import re
import logging

logger = logging.getLogger(__name__)

class PriorityService:
    def __init__(self, high_confidence_threshold: float = 0.8, medium_confidence_threshold: float = 0.55):
        self.high_threshold = high_confidence_threshold
        self.medium_threshold = medium_confidence_threshold
        
        # High intensity or legal risk phrases
        self.escalation_keywords = [
            r"\bsue\b", r"\blawyer\b", r"\blegal\b", r"\bcancel subscription\b", 
            r"\bclose my account\b", r"\brepeatedly\b", r"\bworst service\b",
            r"\bcalling for three days\b", r"\bcalled three times\b"
        ]

    def calculate_priority(self, sentiment: str, confidence: float, issue: str, transcript: str) -> str:
        sentiment = sentiment.lower()
        transcript_lower = transcript.lower() if transcript else ""
        
        # Base classification from Sentiment + Confidence
        if sentiment == "negative":
            if confidence >= self.high_threshold:
                priority = "HIGH"
            elif confidence >= self.medium_threshold:
                priority = "MEDIUM"
            else:
                priority = "NORMAL"
        else:
            priority = "NORMAL"
            
        # Upgrade Rule: Sensitive issues (Refund/Billing) with negative sentiment get boosted
        if sentiment == "negative" and issue in ["Refund", "Billing"] and priority == "NORMAL":
            priority = "MEDIUM"
            
        # Upgrade Rule: Specific anger/escalation trigger phrases
        has_escalation = any(re.search(pattern, transcript_lower) for pattern in self.escalation_keywords)
        if has_escalation:
            if priority == "NORMAL":
                priority = "MEDIUM"
            elif priority == "MEDIUM":
                priority = "HIGH"
                
        logger.info(
            f"Priority calculated: Sentiment={sentiment} ({confidence:.2f}), "
            f"Issue={issue}, EscalationTrigger={has_escalation} -> Priority={priority}"
        )
        return priority

priority_calculator = PriorityService()
