from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI()

# Cấu hình CORS để cho phép file index.html có thể gọi tới server này
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép tất cả các nguồn gốc
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search/")
async def search_image(image: UploadFile = File(...)):
    # In ra tên file trên terminal để bạn biết backend đã nhận được ảnh
    print(f"Backend đã nhận được file: {image.filename}")
    
    # Giả lập thời gian xử lý trong 2 giây
    time.sleep(2)

    # Trả về một danh sách kết quả ảnh cố định
    dummy_results = [
        'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?ixlib=rb-4.0.3&q=80&fm=jpg&crop=faces&fit=crop&h=400&w=400',
        'https://images.unsplash.com/photo-1534528741775-53994a69daeb?ixlib=rb-4.0.3&q=80&fm=jpg&crop=faces&fit=crop&h=400&w=400',
        'https://images.unsplash.com/photo-1521119989659-a83eee488004?ixlib=rb-4.0.3&q=80&fm=jpg&crop=faces&fit=crop&h=400&w=400',
        'https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?ixlib=rb-4.0.3&q=80&fm=jpg&crop=faces&fit=crop&h=400&w=400',
        'https://images.unsplash.com/photo-1544005313-94ddf0286df2?ixlib=rb-4.0.3&q=80&fm=jpg&crop=faces&fit=crop&h=400&w=400',
        'https://images.unsplash.com/photo-1580489944761-15a19d654956?ixlib=rb-4.0.3&q=80&fm=jpg&crop=faces&fit=crop&h=400&w=400',
    ]
    
    return {"matching_images": dummy_results}

