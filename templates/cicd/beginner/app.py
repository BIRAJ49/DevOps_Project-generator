def latest_pipeline_status() -> dict[str, str]:
    return {"service": "build-api", "status": "green"}


if __name__ == "__main__":
    print(latest_pipeline_status())

