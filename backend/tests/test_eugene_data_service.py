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


def test_sidewalk_ramp_normalization_preserves_dimensions():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-123.1, 44.0]},
        "properties": {
            "OBJECTID": 42,
            "Ramp_Configuration": "dual",
            "Curb_RampL_Width": 4.9,
            "Curb_RampR_Width": 5.0,
            "Curb_RampL_Grade": 7.4,
            "Curb_RampR_Grade": 6.8,
            "Curb_RampL_Cross_Slope": 1.1,
            "Curb_RampR_Cross_Slope": 1.4,
        },
    }

    normalized = EugeneDataService._normalize_sidewalk_ramp(feature, 1)
    properties = normalized["properties"]

    assert properties["configuration"] == "dual"
    assert properties["left_width_feet"] == 4.9
    assert properties["right_width_feet"] == 5.0
    assert properties["left_grade_percent"] == 7.4
    assert properties["right_grade_percent"] == 6.8
    assert properties["left_cross_slope_percent"] == 1.1
    assert properties["right_cross_slope_percent"] == 1.4


def test_sidewalk_ramp_zero_width_sentinels_become_null_without_losing_zero_slope():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-123.1, 44.0]},
        "properties": {
            "OBJECTID": 43,
            "Curb_Ramp_Width": 0,
            "Curb_RampL_Width": -1,
            "Curb_RampR_Width": 4.0,
            "Curb_Ramp_Grade": 0,
            "Curb_Ramp_Cross_Slope": 0,
        },
    }

    properties = EugeneDataService._normalize_sidewalk_ramp(feature, 1)["properties"]

    assert properties["width_feet"] is None
    assert properties["left_width_feet"] is None
    assert properties["right_width_feet"] == 4.0
    assert properties["grade_percent"] == 0
    assert properties["cross_slope_percent"] == 0
