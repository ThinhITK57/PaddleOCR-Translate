from fastapi import FastAPI
from api.ocr import router as ocr_router

app = FastAPI()

# Register API routers
app.include_router(ocr_router)
