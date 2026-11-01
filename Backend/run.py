import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print(f"Starting server at http://{settings.HOST}:{settings.PORT} (mock={settings.USE_MOCK_AI})")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
