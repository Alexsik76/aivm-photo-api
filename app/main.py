from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import health, upload, recognize
from app.ml.models import load_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load ML models
    app.state.display_model, app.state.digit_model = load_models()
    yield
    # Clean up if needed
    del app.state.display_model
    del app.state.digit_model

app = FastAPI(
    title="aivm-photo-api",
    version="0.2.0",
    lifespan=lifespan
)

app.include_router(health.router)
app.include_router(upload.router, prefix="/images")
app.include_router(recognize.router, prefix="/images")
