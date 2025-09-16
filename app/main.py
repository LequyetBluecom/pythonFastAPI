import os
import uvicorn
from fastapi import FastAPI

# Khởi tạo app
app = FastAPI()

# Route đơn giản
@app.get("/")
def read_root():
    return {"message": "Hello FastAPI 🚀"}

# Route có tham số
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "query": q}

# Health check endpoint
@app.get("/healthz")
def health_check():
    return {"status": "healthy"}

# Production server entry point
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
