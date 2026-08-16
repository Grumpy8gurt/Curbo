from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health(request: Request):
    """
    Simple liveness probe.  Returns {"status": "ok"} when the server is running.
    Used by Docker health checks and manual verification scripts.
    The service_name is included so that load-balancer logs can identify the
    instance when multiple services are running behind a reverse proxy.
    """
    db_status = request.app.state.db_status
    if (
        request.app.state.settings.resolved_database_url is not None
        and db_status != "connected"
    ):
        return JSONResponse(
            status_code=503,
            content={
                "status": "not-ready",
                "service": request.app.state.settings.service_name,
                "database": db_status,
            },
        )
    return {
        "status": "ok",
        "service": request.app.state.settings.service_name,
    }


@router.get("/live")
def get_liveness(request: Request) -> dict[str, str]:
    """Process-only liveness check; dependency failures do not restart the process."""
    return {"status": "ok", "service": request.app.state.settings.service_name}


@router.get("/ready")
def get_readiness(request: Request):
    """Readiness alias used by orchestrators and load balancers."""
    return get_health(request)
