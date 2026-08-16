def test_report_endpoint_returns_summary_and_download(client):
    road_id = client.get("/api/layers/roads").json()["features"][0]["properties"]["road_id"]
    response = client.post(
        "/api/reports/corridor",
        json={"corridor_id": road_id, "format": "html"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["reportId"].startswith("rep_")
    assert payload["roadId"] == road_id
    assert payload["downloadUrl"].endswith("/download")

    download_response = client.get(payload["downloadUrl"])
    assert download_response.status_code == 200
    assert "CURBO Corridor Report" in download_response.text


def test_report_html_uses_readable_sections_and_screening_limitations(client):
    road_id = client.get("/api/layers/roads").json()["features"][0]["properties"]["road_id"]
    response = client.post(
        "/api/reports/corridor",
        json={"corridor_id": road_id, "format": "html"},
    )

    report_html = client.get(response.json()["downloadUrl"]).text

    assert "Screening Metrics" in report_html
    assert "Review Signals" in report_html
    assert "Data Limitations" in report_html
    assert "current crash, speed, traffic-volume" in report_html
    assert "<pre>" not in report_html


def test_report_rejects_unimplemented_format(client):
    road_id = client.get("/api/layers/roads").json()["features"][0]["properties"]["road_id"]

    response = client.post(
        "/api/reports/corridor",
        json={"corridor_id": road_id, "format": "pdf"},
    )

    assert response.status_code == 422


def test_report_download_survives_app_restart(tmp_path):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'curbo.db'}",
        report_dir=str(tmp_path / "reports"),
        annotation_file=str(tmp_path / "annotations.json"),
    )
    with TestClient(create_app(settings)) as first_client:
        road_id = first_client.get("/api/layers/roads").json()["features"][0]["properties"]["road_id"]
        created = first_client.post(
            "/api/reports/corridor",
            json={"corridor_id": road_id, "format": "html"},
        ).json()

    with TestClient(create_app(settings)) as restarted_client:
        response = restarted_client.get(created["downloadUrl"])

    assert response.status_code == 200
    assert "CURBO Corridor Report" in response.text


def test_report_count_policy_removes_oldest_artifact(tmp_path):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'curbo.db'}",
        report_dir=str(tmp_path / "reports"),
        annotation_file=str(tmp_path / "annotations.json"),
        max_report_files=1,
    )
    with TestClient(create_app(settings)) as limited_client:
        road_id = limited_client.get("/api/layers/roads").json()["features"][0]["properties"]["road_id"]
        first = limited_client.post(
            "/api/reports/corridor", json={"roadId": road_id, "format": "html"}
        ).json()
        second = limited_client.post(
            "/api/reports/corridor", json={"roadId": road_id, "format": "html"}
        ).json()

        first_download = limited_client.get(first["downloadUrl"])
        second_download = limited_client.get(second["downloadUrl"])

    assert first_download.status_code == 404
    assert second_download.status_code == 200
