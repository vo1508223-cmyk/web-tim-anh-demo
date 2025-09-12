import os
import aiofiles
from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import random
from typing import List

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

# API endpoint mới: Lấy danh sách tất cả các sự kiện
@app.get("/events/")
async def get_events():
    try:
        # Lấy danh sách các thư mục con, mỗi thư mục là một sự kiện
        events = [name for name in os.listdir(BASE_EVENT_DIR) if os.path.isdir(os.path.join(BASE_EVENT_DIR, name))]
        return JSONResponse(content={"events": events})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# API endpoint của admin: Tạo sự kiện và tải ảnh lên
@app.post("/create_event/")
async def create_event(event_name: str = Form(...), files: List[UploadFile] = File(...)):
    event_path = os.path.join(BASE_EVENT_DIR, event_name)
    os.makedirs(event_path, exist_ok=True) # Tạo thư mục sự kiện

    for file in files:
        file_path = os.path.join(event_path, file.filename)
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
    return {"message": f"Đã tạo/cập nhật sự kiện '{event_name}' với {len(files)} ảnh."}

# API endpoint của người dùng: Tìm kiếm ảnh trong một sự kiện cụ thể
@app.post("/search/")
async def search_image(request: Request, event_name: str = Form(...), image: UploadFile = File(...)):
    print(f"Backend nhận yêu cầu tìm kiếm trong sự kiện '{event_name}' cho file: {image.filename}")
    
    event_path = os.path.join(BASE_EVENT_DIR, event_name)
    
    # Kiểm tra xem sự kiện có tồn tại không
    if not os.path.isdir(event_path):
        return JSONResponse(content={"matching_images": [], "message": "Sự kiện không tồn tại."}, status_code=404)

    # Lấy danh sách các ảnh trong thư mục sự kiện
    uploaded_images = os.listdir(event_path)
    
    # Trả về ngẫu nhiên một vài ảnh từ sự kiện làm kết quả (demo)
    if uploaded_images:
        num_results = min(len(uploaded_images), 6)
        random_selection = random.sample(uploaded_images, num_results)
        
        base_url = str(request.base_url)
        # Tạo URL đầy đủ, bao gồm cả tên sự kiện
        results_with_urls = [f"{base_url}{BASE_EVENT_DIR}/{event_name}/{img_name}" for img_name in random_selection]
        
        return {"matching_images": results_with_urls}
    
    return {"matching_images": []}

