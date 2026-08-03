from app.schemas.geojson import FeatureCollection


class LayerFeatureCollection(FeatureCollection):
    """
    Thin subclass of FeatureCollection used as the response_model for all
    layer endpoints.  The indirection keeps the OpenAPI schema named
    "LayerFeatureCollection" so the auto-generated docs distinguish layer
    responses from annotation responses.
    """
    pass
