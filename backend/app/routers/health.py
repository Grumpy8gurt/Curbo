from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health(request: Request) -> dict[str, str]:
    """
    Simple liveness probe.  Returns {"status": "ok"} when the server is running.
    Used by Docker health checks and manual verification scripts.
    The service_name is included so that load-balancer logs can identify the
    instance when multiple services are running behind a reverse proxy.
    """
    return {
        "status": "ok",
        "service": request.app.state.settings.service_name,
    }
