from fastapi import FastAPI

app = FastAPI(title="Build Promotion API")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/promotions")
def promotions() -> dict[str, list[dict[str, str]]]:
    return {
        "items": [
            {"environment": "staging", "version": "2026.04.1"},
            {"environment": "production", "version": "2026.03.9"}
        ]
    }

