import re
import logging

logger = logging.getLogger(__name__)

class IssueDetectionService:
    def __init__(self):
        # Helpdesk issue keyword matching categories
        self.rules = {
            "Refund": [
                r"\brefund\b", r"\bmoney back\b", r"\breimburse", r"\breturned my money\b", r"\bchargeback\b"
            ],
            "Billing": [
                r"\bbill\b", r"\bdouble charge\b", r"\binvoice\b", r"\bovercharge\b", r"\bcharged me\b", r"\bfees\b", r"\bpricing\b"
            ],
            "Payment": [
                r"\bpayment\b", r"\bcredit card\b", r"\bpaypal\b", r"\bdeclined\b", r"\btransaction\b", r"\bpay\b"
            ],
            "Technical Issue": [
                r"\berror\b", r"\bbug\b", r"\bbroken\b", r"\bnot working\b", r"\bcrash\b", r"\bslow\b", r"\bglitch\b", r"\bwebsite down\b", r"\bapp down\b"
            ],
            "Account/Login": [
                r"\blogin\b", r"\bpassword\b", r"\baccount\b", r"\breset\b", r"\busername\b", r"\blocked out\b", r"\bsign in\b"
            ],
            "Delivery": [
                r"\bdelivery\b", r"\bshipment\b", r"\bshipping\b", r"\btracking\b", r"\bpackage\b", r"\bnot arrived\b", r"\btransit\b"
            ],
            "Subscription": [
                r"\bsubscription\b", r"\bcancel\b", r"\brenew\b", r"\bmembership\b", r"\bplan\b"
            ],
            "Product Complaint": [
                r"\bdefective\b", r"\bquality\b", r"\bdamaged\b", r"\bproduct\b", r"\bitem\b", r"\bscratch\b", r"\bpoor\b"
            ]
        }

    def detect_issue(self, text: str) -> str:
        if not text or not text.strip():
            return "Other"
            
        text_lower = text.lower()
        scores = {}
        
        for issue, patterns in self.rules.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                score += len(matches)
            if score > 0:
                scores[issue] = score
                
        if not scores:
            return "Other"
            
        # Return issue with highest matches count
        sorted_issues = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_issues[0][0]

issue_detector = IssueDetectionService()
