from fastapi import APIRouter
from ..schemas.requests import DetectSmellRequest
from ..schemas.responses import DetectSmellStaticResponse
from ..utils.static_analysis import detect_static

router = APIRouter()


@router.post("/detect_smell_static", response_model=DetectSmellStaticResponse)
async def detect_smell_static(payload: DetectSmellRequest):
    code_snippet = payload.code_snippet
    analysis_result = detect_static(code_snippet)
    return DetectSmellStaticResponse(
        success=analysis_result["success"],
        smells=analysis_result["response"],
        loc=analysis_result.get("loc"),
        density=analysis_result.get("density"),
        quality=analysis_result.get("quality"),
    )
