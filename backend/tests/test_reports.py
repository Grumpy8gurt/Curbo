def test_report_endpoint_returns_summary_and_download(client):
    response = client.post(
        "/api/reports/corridor",
        json={
            "road_id": "road_1",
            "include_layers": ["curb_ramps", "hydrants", "annotations", "detections"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["report_id"].startswith("report_")
    assert payload["summary"]["road_id"] == "road_1"
    assert payload["download_url"].endswith("/download")

    download_response = client.get(payload["download_url"])
    assert download_response.status_code == 200
    assert "Curbo Corridor Report" in download_response.text
