import type { Feature, FeatureCollection, PointGeometry } from "./geojson";

export type AnnotationKind =
  | "missing curb cut"
  | "bad data"
  | "obstruction"
  | "other";

export interface AnnotationProperties {
  annotation_id: string;
  annotation_type: AnnotationKind;
  description: string;
  status: "pending" | "reviewed" | "confirmed" | "rejected";
  source: string;
  created_at: string;
}

export interface AnnotationDraft {
  annotationType: AnnotationKind;
  description: string;
  latitude: number;
  longitude: number;
}

export type AnnotationFeature = Feature<AnnotationProperties, PointGeometry>;
export type AnnotationFeatureCollection = FeatureCollection<AnnotationFeature>;
