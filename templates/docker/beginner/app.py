from fastapi import FastAPI

app = FastAPI(title="Release Notes Service")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/releases/latest")
def latest_release() -> dict[str, str]:
    return {
        "version": "v1.0.0",
        "summary": "Initial containerized release with health checks.",
    }

