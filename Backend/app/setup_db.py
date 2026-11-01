import asyncio
from datetime import datetime, timedelta
import random
import sys
import os

# Append project path to ensure imports work from this directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

SAMPLE_CALLS = [
    {
        "filename": "call_cust_refund_angry.wav",
        "duration": 142.5,
        "transcript": "I have been waiting for my refund for a week. Nobody has solved my billing issue! I want my money back or I will sue your company.",
        "sentiment_label": "negative",
        "sentiment_confidence": 0.96,
        "detected_issue": "Refund",
        "priority": "HIGH",
        "processing_status": "completed",
    },
    {
        "filename": "call_technical_resolved.mp3",
        "duration": 85.0,
        "transcript": "Thank you so much. The tech issue with the software is finally resolved and it runs perfectly. The support agent was awesome.",
        "sentiment_label": "positive",
        "sentiment_confidence": 0.94,
        "detected_issue": "Technical Issue",
        "priority": "NORMAL",
        "processing_status": "completed",
    },
    {
        "filename": "call_status_check.wav",
        "duration": 45.2,
        "transcript": "Hi, I just wanted to know the status of my ticket for the login issue. Can you check my account status?",
        "sentiment_label": "neutral",
        "sentiment_confidence": 0.82,
        "detected_issue": "Account/Login",
        "priority": "NORMAL",
        "processing_status": "completed",
    },
    {
        "filename": "call_double_billing.m4a",
        "duration": 110.0,
        "transcript": "I am looking at my monthly invoice and I was charged twice for the subscription this month. Please cancel my extra charge.",
        "sentiment_label": "negative",
        "sentiment_confidence": 0.88,
        "detected_issue": "Billing",
        "priority": "HIGH",
        "processing_status": "completed",
    },
    {
        "filename": "call_cancel_subscription.mp3",
        "duration": 190.5,
        "transcript": "This is unacceptable. I have called repeatedly to cancel my membership, but I was charged again. Close my account immediately.",
        "sentiment_label": "negative",
        "sentiment_confidence": 0.95,
        "detected_issue": "Subscription",
        "priority": "HIGH",
        "processing_status": "completed",
    },
    {
        "filename": "call_delivery_delay.wav",
        "duration": 65.0,
        "transcript": "Hello, my tracking number says the package has been in transit for five days. Can you tell me when it will arrive?",
        "sentiment_label": "negative",
        "sentiment_confidence": 0.65,
        "detected_issue": "Delivery",
        "priority": "MEDIUM",
        "processing_status": "completed",
    },
    {
        "filename": "call_payment_failed.mp3",
        "duration": 78.4,
        "transcript": "I tried to update my credit card details, but the payment transaction was declined. Please help me clear the subscription charge.",
        "sentiment_label": "neutral",
        "sentiment_confidence": 0.58,
        "detected_issue": "Payment",
        "priority": "NORMAL",
        "processing_status": "completed",
    },
    {
        "filename": "call_complaint_damaged_product.wav",
        "duration": 135.2,
        "transcript": "I received my order today, but the package was completely smashed and the item inside is cracked. This is defective quality.",
        "sentiment_label": "negative",
        "sentiment_confidence": 0.89,
        "detected_issue": "Product Complaint",
        "priority": "MEDIUM",
        "processing_status": "completed",
    },
    {
        "filename": "call_general_question.mp3",
        "duration": 35.0,
        "transcript": "Yes, I am planning to upgrade my plan next month. Could you explain the differences between the gold and silver subscriptions?",
        "sentiment_label": "neutral",
        "sentiment_confidence": 0.88,
        "detected_issue": "Subscription",
        "priority": "NORMAL",
        "processing_status": "completed",
    },
    {
        "filename": "call_login_success.wav",
        "duration": 50.0,
        "transcript": "Awesome, the password reset email came through. I have updated it and I can sign in to my dashboard now. Thanks!",
        "sentiment_label": "positive",
        "sentiment_confidence": 0.98,
        "detected_issue": "Account/Login",
        "priority": "NORMAL",
        "processing_status": "completed",
    }
]

async def seed_database():
    print(f"Connecting to MongoDB at {settings.MONGODB_URL}...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    collection = db["calls"]
    
    print("Dropping existing calls collection...")
    await collection.drop()
    
    docs = []
    base_time = datetime.utcnow()
    
    # Seed 15 items with distributed timestamps
    for i in range(15):
        sample = SAMPLE_CALLS[i % len(SAMPLE_CALLS)]
        
        # Spread calls out over the last 5 days
        call_time = base_time - timedelta(
            days=random.randint(0, 4),
            hours=random.randint(1, 23),
            minutes=random.randint(1, 59)
        )
        
        doc = {
            "call_id": f"seed-uuid-00000000-0000-0000-0000-{i:012d}",
            "filename": sample["filename"],
            "filepath": f"data/uploads/{sample['filename']}",
            "upload_time": call_time,
            "duration": sample["duration"] + random.randint(-10, 15),
            "transcript": sample["transcript"],
            "sentiment_label": sample["sentiment_label"],
            "sentiment_confidence": sample["sentiment_confidence"],
            "detected_issue": sample["detected_issue"],
            "priority": sample["priority"],
            "processing_status": sample["processing_status"],
            "error_message": None,
            "created_at": call_time,
            "updated_at": call_time
        }
        docs.append(doc)
        
    result = await collection.insert_many(docs)
    print(f"Successfully seeded database with {len(result.inserted_ids)} records!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
