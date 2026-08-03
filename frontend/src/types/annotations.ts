import type {
  Feature,
  FeatureCollection,
  LineStringGeometry,
  PointGeometry
} from "./geojson";

// Full set of annotation categories — kept in sync with the backend Literal
// type in schemas/annotations.py.  The backend currently enforces a subset;
// extending either side requires updating both.
export type AnnotationKind =
  | "curb cut"
  | "missing curb cut"
  | "fire hydrant"
  | "bike lane gap"
  | "proposed bike lane"
  | "bad data"
  | "obstruction"
  | "parking/loading conflict"
  | "intersection safety"
  | "drainage/utility conflict"
  | "other";

// Annotations can be either a point (spot issue) or a line (corridor issue).
export type AnnotationGeometry = PointGeometry | LineStringGeometry;
export type AnnotationDrawMode = "point" | "line";
export type AnnotationStatus = "pending" | "reviewed" | "confirmed" | "rejected";

export interface AnnotationProperties {
  annotation_id: string;
  annotation_type: AnnotationKind;
  description: string;
  // Status lifecycle: pending → reviewed → confirmed | rejected
  status: AnnotationStatus;
  source: string;
  // ISO 8601 string (the backend serialises datetime to isoformat before sending).
  created_at: string;
}

/**
 * Draft used by the AnnotationTool form before the annotation is persisted.
 * Uses a GeoJSON geometry directly rather than lat/lng fields to support both
 * point and line draw modes.
 */
export interface AnnotationDraft {
  annotationType: AnnotationKind;
  description: string;
  geometry: AnnotationGeometry;
}

export type AnnotationFeature = Feature<AnnotationProperties, AnnotationGeometry>;
export type AnnotationFeatureCollection = FeatureCollection<AnnotationFeature>;
