def test_corridor_analysis_returns_expected_fields(client):
    response = client.post(
        "/api/corridors/analyze",
        json={"roadId": "rd_001"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["roadId"] == "rd_001"
    assert "knownCurbRamps" in payload
    assert "bikeLaneFeasibility" in payload
    assert isinstance(payload["planningNotes"], list)
