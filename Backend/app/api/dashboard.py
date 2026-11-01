import logging
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Query, status

from app.core.database import db
from app.schemas.dashboard import (
    SummaryCards,
    SentimentDistributionItem,
    SentimentTrendItem,
    IssueMetricItem
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=SummaryCards)
async def get_summary_metrics():
    collection = db.get_collection("calls")
    total = await collection.count_documents({})
    
    pipeline = [
        {
            "$facet": {
                "positive": [{"$match": {"sentiment_label": "positive"}}, {"$count": "count"}],
                "neutral": [{"$match": {"sentiment_label": "neutral"}}, {"$count": "count"}],
                "negative": [{"$match": {"sentiment_label": "negative"}}, {"$count": "count"}],
                "high_priority": [{"$match": {"priority": "HIGH"}}, {"$count": "count"}]
            }
        }
    ]
    
    try:
        cursor = collection.aggregate(pipeline)
        res = await cursor.to_list(length=1)
        
        positive = 0
        neutral = 0
        negative = 0
        high_priority = 0
        
        if res:
            facet = res[0]
            positive = facet["positive"][0]["count"] if facet["positive"] else 0
            neutral = facet["neutral"][0]["count"] if facet["neutral"] else 0
            negative = facet["negative"][0]["count"] if facet["negative"] else 0
            high_priority = facet["high_priority"][0]["count"] if facet["high_priority"] else 0
            
        return {
            "total_calls": total,
            "positive_calls": positive,
            "neutral_calls": neutral,
            "negative_calls": negative,
            "high_priority_calls": high_priority
        }
    except Exception as e:
        logger.error(f"Dashboard summary extraction failed: {e}")
        return {
            "total_calls": total,
            "positive_calls": 0,
            "neutral_calls": 0,
            "negative_calls": 0,
            "high_priority_calls": 0
        }

@router.get("/sentiment-distribution", response_model=List[SentimentDistributionItem])
async def get_sentiment_distribution():
    collection = db.get_collection("calls")
    total = await collection.count_documents({"sentiment_label": {"$ne": None}})
    
    pipeline = [
        {"$match": {"sentiment_label": {"$ne": None}}},
        {"$group": {"_id": "$sentiment_label", "count": {"$sum": 1}}}
    ]
    
    try:
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=10)
        found_labels = {r["_id"]: r["count"] for r in results}
        
        dist = []
        for label in ["positive", "neutral", "negative"]:
            count = found_labels.get(label, 0)
            percentage = (count / total * 100) if total > 0 else 0
            dist.append({
                "name": label.capitalize(),
                "value": count,
                "percentage": round(percentage, 2)
            })
        return dist
    except Exception as e:
        logger.error(f"Sentiment distribution aggregation failed: {e}")
        return []

@router.get("/sentiment-trends", response_model=List[SentimentTrendItem])
async def get_sentiment_trends(days: int = Query(7, ge=1, le=90)):
    collection = db.get_collection("calls")
    start_date = datetime.utcnow() - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "upload_time": {"$gte": start_date},
                "sentiment_label": {"$ne": None}
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$upload_time"}
                },
                "positive": {
                    "$sum": {"$cond": [{"$eq": ["$sentiment_label", "positive"]}, 1, 0]}
                },
                "neutral": {
                    "$sum": {"$cond": [{"$eq": ["$sentiment_label", "neutral"]}, 1, 0]}
                },
                "negative": {
                    "$sum": {"$cond": [{"$eq": ["$sentiment_label", "negative"]}, 1, 0]}
                }
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    try:
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=days + 10)
        
        trends = []
        for r in results:
            trends.append({
                "date": r["_id"],
                "positive": r["positive"],
                "neutral": r["neutral"],
                "negative": r["negative"]
            })
            
        # Ensure fallback empty calendar days are returned if database is empty
        if not trends:
            for i in range(days - 1, -1, -1):
                date_str = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
                trends.append({
                    "date": date_str,
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                })
        return trends
    except Exception as e:
        logger.error(f"Sentiment trends aggregation failed: {e}")
        return []

@router.get("/issues", response_model=List[IssueMetricItem])
async def get_issues_metrics():
    collection = db.get_collection("calls")
    total_with_issues = await collection.count_documents({"detected_issue": {"$ne": None}})
    
    pipeline = [
        {"$match": {"detected_issue": {"$ne": None}}},
        {
            "$group": {
                "_id": "$detected_issue",
                "count": {"$sum": 1},
                "negative_count": {
                    "$sum": {"$cond": [{"$eq": ["$sentiment_label", "negative"]}, 1, 0]}
                }
            }
        },
        {"$sort": {"count": -1}}
    ]
    
    try:
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=50)
        
        metrics = []
        for r in results:
            count = r["count"]
            neg_count = r["negative_count"]
            percentage = (count / total_with_issues * 100) if total_with_issues > 0 else 0
            neg_percentage = (neg_count / count * 100) if count > 0 else 0
            
            metrics.append({
                "issue": r["_id"],
                "count": count,
                "percentage": round(percentage, 2),
                "negative_count": neg_count,
                "negative_percentage": round(neg_percentage, 2)
            })
        return metrics
    except Exception as e:
        logger.error(f"Issue analytics extraction failed: {e}")
        return []
