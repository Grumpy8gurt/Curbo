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
