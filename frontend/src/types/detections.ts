import type { Feature, FeatureCollection, PointGeometry } from "./geojson";

export type DetectionReviewStatus = "pending" | "confirmed" | "rejected";

export interface DetectionProperties {
  detection_id: string;
  label: string;
  confidence: number;
  review_status: DetectionReviewStatus;
  source: string;
  upload_id?: string;
  bbox?: [number, number, number, number];
}

export type DetectionFeature = Feature<DetectionProperties, PointGeometry>;
export type DetectionFeatureCollection = FeatureCollection<DetectionFeature>;
