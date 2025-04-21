from pathlib import Path
import sys
module_path = Path(__file__).parent
sys.path.append(str(module_path))

from fastapi import FastAPI
from api.frame.frame_routes import router as frame_router

app = FastAPI()

app.include_router(frame_router, prefix="/api/save/frame", tags=["진단용 이미지 저장"])

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
