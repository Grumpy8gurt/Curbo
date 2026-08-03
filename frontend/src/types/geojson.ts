/**
 * Minimal GeoJSON type definitions used throughout the frontend.
 *
 * These mirror RFC 7946 but are intentionally narrower — only the geometry
 * types actually present in the Eugene GIS layers are modelled.  The optional
 * metadata extension on FeatureCollection is a CURBO-specific addition used
 * to carry layer status and source attribution from the backend.
 */

// Position uses a tuple type to enforce the GeoJSON [longitude, latitude] order
// at the type level, preventing accidental (lat, lng) argument transposition.
export type Position = [number, number];

export interface PointGeometry {
  type: "Point";
  coordinates: Position;
}

export interface LineStringGeometry {
  type: "LineString";
  coordinates: Position[];
}

export interface MultiLineStringGeometry {
  type: "MultiLineString";
  coordinates: Position[][];
}

export interface PolygonGeometry {
  type: "Polygon";
  coordinates: Position[][];
}

export type Geometry =
  | PointGeometry
  | LineStringGeometry
  | MultiLineStringGeometry
  | PolygonGeometry;

/**
 * Generic GeoJSON Feature parameterised on Properties and geometry Shape.
 * Default type parameters allow untyped usages like `Feature` when the
 * specific layer type is not known at the call site.
 */
export interface Feature<
  Properties extends object = Record<string, unknown>,
  Shape extends Geometry = Geometry
> {
  type: "Feature";
  id?: string | number;
  properties: Properties;
  geometry: Shape;
}

/**
 * Generic GeoJSON FeatureCollection parameterised on Feature type.
 * The optional metadata field is outside the RFC 7946 spec but is consumed
 * by the LayerPanel to show data source and freshness to planners.
 */
export interface FeatureCollection<
  Item extends Feature<object, Geometry> = Feature
> {
  type: "FeatureCollection";
  features: Item[];
  metadata?: {
    layer?: string;
    status?: string;
    source?: string;
  };
}
