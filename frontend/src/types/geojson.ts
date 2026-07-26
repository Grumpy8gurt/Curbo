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

export interface Feature<
  Properties extends object = Record<string, unknown>,
  Shape extends Geometry = Geometry
> {
  type: "Feature";
  id?: string | number;
  properties: Properties;
  geometry: Shape;
}

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
