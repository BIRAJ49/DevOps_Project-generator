from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Deployment Tracker API")


class DeploymentRequest(BaseModel):
    service: str
    version: str


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/deployments")
def create_deployment(request: DeploymentRequest) -> dict[str, str]:
    return {
        "message": "Deployment accepted for asynchronous processing.",
        "service": request.service,
        "version": request.version,
    }

