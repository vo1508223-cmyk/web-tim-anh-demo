import os
import aiofiles
import face_recognition
import numpy as np
import io
import shutil
from PIL import Image

from fastapi import FastAPI, File, UploadFile, Request, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn

# Thư mục gốc chứa tất cả các sự kiện
BASE_EVENT_DIR = "all_events_real"
os.makedirs(BASE_EVENT_DIR, exist_ok=True)

app = FastAPI()

# Phục vụ các file trong thư mục sự kiện để trình duyệt có thể xem được
app.mount(f"/{BASE_EVENT_DIR}", StaticFiles(directory=BASE_EVENT_DIR), name="events")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def process_and_save_encodings(image_bytes, base_path):
    """
    Tìm tất cả các khuôn mặt trong một ảnh, tính toán encoding và lưu chúng.
    Mỗi khuôn mặt tìm thấy sẽ được lưu thành một file .npy riêng.
    """
    try:
        image = face_recognition.load_image_file(io.BytesIO(image_bytes))
        face_encodings = face_recognition.face_encodings(image)
        
        for i, face_encoding in enumerate(face_encodings):
            encoding_path = f"{base_path}_{i}.npy"
            np.save(encoding_path, face_encoding)
        return len(face_encodings)
    except Exception as e:
        print(f"Lỗi xử lý ảnh {base_path}: {e}")
        return 0

# --- API cho Người dùng ---

@app.get("/events/")
async def get_events():
    """Lấy danh sách tất cả các sự kiện đã được tạo."""
    try:
        events = [name for name in os.listdir(BASE_EVENT_DIR) if os.path.isdir(os.path.join(BASE_EVENT_DIR, name))]
        return JSONResponse(content={"events": events})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/search/")
async def search_image(request: Request, event_name: str = Form(...), image: UploadFile = File(...)):
    """(Người dùng) Tìm kiếm ảnh dựa trên nhận diện khuôn mặt."""
    event_path = os.path.join(BASE_EVENT_DIR, event_name)
    if not os.path.isdir(event_path):
        return JSONResponse(content={"matching_images": [], "message": "Sự kiện không tồn tại."}, status_code=404)

    try:
        # 1. Tải tất cả các encoding đã được lưu của sự kiện
        known_face_encodings = []
        known_face_filenames = []
        for filename in os.listdir(event_path):
            if filename.endswith(".npy"):
                encoding = np.load(os.path.join(event_path, filename))
                known_face_encodings.append(encoding)
                # Tách tên file gốc từ file .npy
                base_name = filename.rsplit('_', 1)[0]
                # Thử các phần mở rộng ảnh phổ biến
                for ext in ['.jpg', '.jpeg', '.png']:
                    if os.path.exists(base_name + ext):
                        known_face_filenames.append(os.path.basename(base_name + ext))
                        break

        if not known_face_encodings:
             return {"matching_images": [], "message": "Không có khuôn mặt nào trong dữ liệu sự kiện để so sánh."}

        # 2. Xử lý ảnh người dùng tải lên
        user_image_bytes = await image.read()
        user_image = face_recognition.load_image_file(io.BytesIO(user_image_bytes))
        user_face_encodings = face_recognition.face_encodings(user_image)

        if not user_face_encodings:
            return {"matching_images": [], "message": "Không tìm thấy khuôn mặt trong ảnh bạn tải lên."}
        
        user_face_encoding = user_face_encodings[0]

        # 3. So sánh và tìm kết quả
        matches = face_recognition.compare_faces(known_face_encodings, user_face_encoding, tolerance=0.55)
        
        matching_filenames = set()
        for i, match in enumerate(matches):
            if match:
                matching_filenames.add(known_face_filenames[i])
        
        # 4. Tạo URL đầy đủ cho các ảnh khớp
        base_url = str(request.base_url)
        results_with_urls = [f"{base_url}{BASE_EVENT_DIR}/{event_name}/{img_name}" for img_name in matching_filenames]
        
        return {"matching_images": results_with_urls}

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tìm kiếm: {e}")
        return JSONResponse(content={"error": "Đã xảy ra lỗi trong quá trình xử lý ảnh."}, status_code=500)

# --- API cho Admin ---

@app.post("/admin/events/")
async def create_or_add_to_event(event_name: str = Form(...), files: List[UploadFile] = File(...)):
    """
    (Admin) Tạo sự kiện mới hoặc thêm ảnh vào sự kiện đã có.
    Sau đó xử lý nhận diện khuôn mặt cho các ảnh mới.
    """
    event_path = os.path.join(BASE_EVENT_DIR, event_name)
    is_new_event = not os.path.isdir(event_path)
    os.makedirs(event_path, exist_ok=True)
    
    total_faces_found = 0
    for file in files:
        file_path = os.path.join(event_path, file.filename)
        base_path, _ = os.path.splitext(file_path)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        total_faces_found += process_and_save_encodings(content, base_path)
    
    action = "Đã tạo" if is_new_event else "Đã thêm ảnh vào"
    return {"message": f"{action} sự kiện '{event_name}' với {len(files)} ảnh. Tìm thấy và lưu trữ {total_faces_found} khuôn mặt mới."}

@app.get("/admin/events/{event_name}/images/")
async def get_event_images(request: Request, event_name: str):
    """(Admin) Lấy danh sách URL của tất cả ảnh trong một sự kiện."""
    event_path = os.path.join(BASE_EVENT_DIR, event_name)
    if not os.path.isdir(event_path):
        raise HTTPException(status_code=404, detail="Sự kiện không tồn tại")
    
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
    image_names = [f for f in os.listdir(event_path) if f.lower().endswith(image_extensions)]
    
    base_url = str(request.base_url)
    image_urls = [f"{base_url}{BASE_EVENT_DIR}/{event_name}/{img_name}" for img_name in image_names]
    
    return {"images": image_urls}

@app.delete("/admin/events/{event_name}/")
async def delete_event(event_name: str):
    """(Admin) Xóa toàn bộ một sự kiện."""
    event_path = os.path.join(BASE_EVENT_DIR, event_name)
    if not os.path.isdir(event_path):
        raise HTTPException(status_code=404, detail="Sự kiện không tồn tại")
    
    try:
        shutil.rmtree(event_path)
        return {"message": f"Đã xóa thành công sự kiện '{event_name}'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa thư mục sự kiện: {e}")

@app.delete("/admin/events/{event_name}/images/{image_name}")
async def delete_image_from_event(event_name: str, image_name: str):
    """(Admin) Xóa một ảnh cụ thể và các file encoding liên quan của nó."""
    event_path = os.path.join(BASE_EVENT_DIR, event_name)
    image_path = os.path.join(event_path, image_name)
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Ảnh không tồn tại")

    try:
        # Xóa file ảnh
        os.remove(image_path)
        
        # Xóa tất cả các file .npy có cùng tên gốc
        base_name, _ = os.path.splitext(image_path)
        for f in os.listdir(event_path):
            if f.startswith(os.path.basename(base_name)) and f.endswith('.npy'):
                os.remove(os.path.join(event_path, f))
                
        return {"message": f"Đã xóa thành công ảnh '{image_name}' khỏi sự kiện '{event_name}'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa ảnh: {e}")

# --- (Công tắc tự động) ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

