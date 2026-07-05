from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health(request: Request) -> dict[str, str]:
    return {
        "status": "ok",
        "service": request.app.state.settings.service_name,
    }
