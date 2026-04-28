def deployment_report() -> dict[str, str]:
    return {"environment": "staging", "strategy": "rolling"}


if __name__ == "__main__":
    print(deployment_report())

