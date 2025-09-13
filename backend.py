import os
import shutil
import random
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Khởi tạo app
app = FastAPI()

# Thư mục lưu dữ liệu
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Gắn static để xem ảnh
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Bộ nhớ tạm để quản lý sự kiện
events = {}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>Web tìm ảnh sự kiện (Demo)</h1>
    <p>Vào <a href='/index.html'>Giao diện chính</a></p>
    """

# Endpoint tạo sự kiện + upload nhiều ảnh
@app.post("/create_event/")
async def create_event(event_id: str = Form(...), files: list[UploadFile] = File(...)):
    folder = os.path.join(UPLOAD_DIR, event_id)
    os.makedirs(folder, exist_ok=True)

    paths = []
    for f in files:
        file_path = os.path.join(folder, f.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)
        paths.append(file_path)

    events[event_id] = {"photos": paths}
    return {"message": "Đã tạo sự kiện", "event_id": event_id, "photos": paths}

# Endpoint lấy danh sách sự kiện
@app.get("/events/")
def list_events():
    return {"events": list(events.keys())}

# Endpoint tìm ảnh (Dummy mode: random ảnh)
@app.post("/search/")
async def search_face(event_id: str = Form(...), file: UploadFile = File(...)):
    if event_id not in events:
        return {"error": "Sự kiện không tồn tại"}

    all_photos = events[event_id]["photos"]
    random_selection = random.sample(all_photos, min(5, len(all_photos)))

    return {"results": [f"/{path}" for path in random_selection]}
