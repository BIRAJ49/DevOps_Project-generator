from app import latest_pipeline_status


def test_latest_pipeline_status() -> None:
    assert latest_pipeline_status()["status"] == "green"

