from fastapi import APIRouter, File, UploadFile, Depends, Request
from app.auth import require_token
from app.schemas import RecognizeResponse
from app.ml.pipeline import recognize as run_pipeline

router = APIRouter()

@router.post(
    "/recognize",
    response_model=RecognizeResponse,
    tags=["images"],
    dependencies=[Depends(require_token)],
)
async def recognize_image(
    request: Request,
    file: UploadFile = File(...),
) -> RecognizeResponse:
    content = await file.read()
    
    # We use app.state to get the loaded models
    display_model = request.app.state.display_model
    digit_model = request.app.state.digit_model
    
    result = run_pipeline(content, display_model, digit_model)
    return RecognizeResponse(**result)
