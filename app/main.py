from fastapi import FastAPI

# Khởi tạo app
app = FastAPI()

# Route đơn giản
@app.get("/")
def read_root():
    return {"message": "Hello FastAPI 🚀"}

# Route có tham số
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}
