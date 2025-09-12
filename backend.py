import os
import aiofiles
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import random
from typing import List

# Tạo thư mục để lưu ảnh sự kiện nếu chưa có
EVENT_PHOTOS_DIR = "event_photos"
os.makedirs(EVENT_PHOTOS_DIR, exist_ok=True)

app = FastAPI()

# Phục vụ các file trong thư mục event_photos để trình duyệt có thể xem được
app.mount(f"/{EVENT_PHOTOS_DIR}", StaticFiles(directory=EVENT_PHOTOS_DIR), name="event_photos")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoint mới để upload nhiều ảnh sự kiện
@app.post("/upload_event/")
async def upload_event_images(files: List[UploadFile] = File(...)):
    for file in files:
        file_path = os.path.join(EVENT_PHOTOS_DIR, file.filename)
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
    return {"message": f"Đã tải lên thành công {len(files)} ảnh."}

# API endpoint tìm kiếm được nâng cấp
@app.post("/search/")
async def search_image(request: Request, image: UploadFile = File(...)):
    print(f"Backend đã nhận được file tìm kiếm: {image.filename}")
    
    # Lấy danh sách các ảnh đã được upload trong sự kiện
    uploaded_images = os.listdir(EVENT_PHOTOS_DIR)
    
    # Trả về ngẫu nhiên một vài ảnh từ sự kiện làm kết quả (demo)
    # Trong phiên bản thật, đây sẽ là nơi xử lý nhận diện khuôn mặt
    if uploaded_images:
        num_results = min(len(uploaded_images), 6) # Trả về tối đa 6 ảnh
        random_selection = random.sample(uploaded_images, num_results)
        
        # Tạo URL đầy đủ để trình duyệt có thể hiển thị
        base_url = str(request.base_url)
        results_with_urls = [f"{base_url}{EVENT_PHOTOS_DIR}/{img_name}" for img_name in random_selection]
        
        return {"matching_images": results_with_urls}
    
    return {"matching_images": []}

