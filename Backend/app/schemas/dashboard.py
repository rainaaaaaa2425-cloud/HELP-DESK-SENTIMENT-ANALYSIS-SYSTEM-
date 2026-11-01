from typing import List, Dict, Any
from pydantic import BaseModel

class SummaryCards(BaseModel):
    total_calls: int
    positive_calls: int
    neutral_calls: int
    negative_calls: int
    high_priority_calls: int

class SentimentDistributionItem(BaseModel):
    name: str  # "Positive", "Neutral", "Negative"
    value: int
    percentage: float

class SentimentTrendItem(BaseModel):
    date: str  # YYYY-MM-DD
    positive: int
    neutral: int
    negative: int

class IssueMetricItem(BaseModel):
    issue: str
    count: int
    percentage: float
    negative_count: int
    negative_percentage: float
