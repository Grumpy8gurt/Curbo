def test_report_endpoint_returns_summary_and_download(client):
    response = client.post(
        "/api/reports/corridor",
        json={"corridor_id": "rd_001", "format": "html"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["reportId"].startswith("rep_")
    assert payload["roadId"] == "rd_001"
    assert payload["downloadUrl"].endswith("/download")

    download_response = client.get(payload["downloadUrl"])
    assert download_response.status_code == 200
    assert "Curbo Corridor Report" in download_response.text
