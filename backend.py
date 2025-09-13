import os
import aiofiles
from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn # Thêm dòng này

# Thư mục gốc chứa tất cả các sự kiện
BASE_EVENT_DIR = "all_events"
os.makedirs(BASE_EVENT_DIR, exist_ok=True)

app = FastAPI()

# Phục vụ các file trong thư mục all_events để trình duyệt có thể xem được
app.mount(f"/{BASE_EVENT_DIR}", StaticFiles(directory=BASE_EVENT_DIR), name="events")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/events/")
async def get_events():
    """Lấy danh sách tất cả các sự kiện đã được tạo."""
    try:
        events = [name for name in os.listdir(BASE_EVENT_DIR) if os.path.isdir(os.path.join(BASE_EVENT_DIR, name))]
        return JSONResponse(content={"events": events})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/create_event/")
async def create_event(event_name: str = Form(...), files: List[UploadFile] = File(...)):
    """(Admin) Tạo sự kiện mới và tải ảnh lên."""
    event_path = os.path.join(BASE_EVENT_DIR, event_name)
    os.makedirs(event_path, exist_ok=True)

    for file in files:
        file_path = os.path.join(event_path, file.filename)
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
    return {"message": f"Đã tạo/cập nhật sự kiện '{event_name}' với {len(files)} ảnh."}

@app.post("/search/")
async def search_image(request: Request, event_name: str = Form(...), image: UploadFile = File(...)):
    """(Người dùng) Tìm kiếm ảnh trong một sự kiện."""
    print(f"Backend nhận yêu cầu tìm kiếm trong sự kiện '{event_name}' cho file: {image.filename}")
    
    event_path = os.path.join(BASE_EVENT_DIR, event_name)
    
    if not os.path.isdir(event_path):
        return JSONResponse(content={"matching_images": [], "message": "Sự kiện không tồn tại."}, status_code=404)

    # --- (DEMO LOGIC - Lô-gic Tìm kiếm Thông minh hơn) ---
    # Logic này không phải là nhận diện khuôn mặt thật.
    # Nó tìm kiếm dựa trên sự trùng khớp một phần của tên file.
    # Ví dụ: nếu người dùng tải lên "khang.jpg", nó sẽ tìm các ảnh sự kiện có chữ "khang" trong tên.
    
    matching_images = []
    try:
        # Lấy phần tên của file người dùng tải lên (ví dụ: "khang" từ "khang.jpg")
        search_keyword = os.path.splitext(image.filename)[0].lower().split('_')[0]

        all_event_images = os.listdir(event_path)
        for img_name in all_event_images:
            if search_keyword in img_name.lower():
                matching_images.append(img_name)
    except Exception as e:
        print(f"Lỗi khi tìm kiếm: {e}")
        # Nếu có lỗi, trả về toàn bộ ảnh như một phương án dự phòng
        matching_images = os.listdir(event_path)[:6] # Giới hạn 6 ảnh

    base_url = str(request.base_url)
    results_with_urls = [f"{base_url}{BASE_EVENT_DIR}/{event_name}/{img_name}" for img_name in matching_images]
        
    return {"matching_images": results_with_urls}

# --- (Công tắc tự động) ---
# Đoạn code này sẽ tự động bật server khi bạn chạy file này.
# Nó giúp việc chạy trên Replit trở nên cực kỳ đơn giản.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

