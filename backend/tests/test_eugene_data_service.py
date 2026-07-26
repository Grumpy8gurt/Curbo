from app.config import Settings
from app.services.eugene_data_service import EugeneDataService


def test_missing_eugene_files_use_documented_fallbacks(tmp_path):
    settings = Settings(database_url="sqlite://")
    collections = EugeneDataService(tmp_path, settings.sample_data_dir).load_all()

    assert collections["roads"]["features"]
    assert collections["roads"]["metadata"]["status"] == "sample-fallback"
    assert collections["curb_ramps"]["metadata"]["status"] == "sample-fallback"
    assert collections["hydrants"]["metadata"]["status"] == "sample-fallback"
    assert collections["bike_lanes"]["features"] == []
    assert collections["bike_lanes"]["metadata"]["status"] == "unavailable"


def test_road_normalization_does_not_duplicate_prefix():
    feature = {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": [[-123.1, 44.0], [-123.0, 44.1]]},
        "properties": {"road_id": "road_example", "name": "Example"},
    }

    normalized = EugeneDataService._normalize_road(feature, 1)

    assert normalized["properties"]["road_id"] == "road_example"
