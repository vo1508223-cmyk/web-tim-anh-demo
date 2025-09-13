import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import face_recognition
import numpy as np

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
    <h1>Web tìm ảnh theo khuôn mặt</h1>
    <p>Vào <a href='/index.html'>giao diện tìm ảnh</a></p>
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

# Endpoint tìm ảnh theo khuôn mặt
@app.post("/search/")
async def search_face(event_id: str = Form(...), file: UploadFile = File(...)):
    if event_id not in events:
        return {"error": "Sự kiện không tồn tại"}

    # Lưu ảnh query
    query_path = os.path.join(UPLOAD_DIR, f"query_{file.filename}")
    with open(query_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Load và mã hóa khuôn mặt query
    query_img = face_recognition.load_image_file(query_path)
    query_encs = face_recognition.face_encodings(query_img)
    if len(query_encs) == 0:
        return {"error": "Không phát hiện khuôn mặt trong ảnh tải lên"}
    query_enc = query_encs[0]

    # So khớp với ảnh trong sự kiện
    matches = []
    for photo in events[event_id]["photos"]:
        img = face_recognition.load_image_file(photo)
        encs = face_recognition.face_encodings(img)
        if len(encs) > 0:
            dist = np.linalg.norm(encs[0] - query_enc)
            matches.append((dist, photo))

    if not matches:
        return {"error": "Không tìm thấy khuôn mặt trong sự kiện"}

    # Sắp xếp theo độ giống (càng nhỏ càng giống)
    matches.sort(key=lambda x: x[0])
    top_matches = [m[1] for m in matches[:5]]  # lấy 5 ảnh giống nhất

    return {"results": [f"/{path}" for path in top_matches]}
