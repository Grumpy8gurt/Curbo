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
