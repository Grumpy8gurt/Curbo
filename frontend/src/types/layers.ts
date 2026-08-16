import type {
  Feature,
  FeatureCollection,
  LineStringGeometry,
  MultiLineStringGeometry,
  PointGeometry
} from "./geojson";

// Union of all layer keys used as map source/layer IDs and visibility toggle keys.
export type LayerId =
  | "roads"
  | "sidewalkRamps"
  | "hydrants"
  | "annotations"
  | "bikeLanes";

// --- Per-layer property interfaces ---
// These mirror the backend normalised schema so TypeScript catches mismatches
// between the API response and the frontend rendering code.

export interface RoadProperties {
  road_id: string;
  name: string;
  classification: string;
}

export interface CurbRampProperties {
  ramp_id: string;
  status: string;
  condition: string;
  configuration?: string;
  width_feet?: number | null;
  left_width_feet?: number | null;
  right_width_feet?: number | null;
  grade_percent?: number | null;
  left_grade_percent?: number | null;
  right_grade_percent?: number | null;
  cross_slope_percent?: number | null;
  left_cross_slope_percent?: number | null;
  right_cross_slope_percent?: number | null;
  source?: string;
}

export interface HydrantProperties {
  hydrant_id: string;
  flow_class: string;
  owner?: string;
  source?: string;
}

export interface BikeLaneProperties {
  bike_lane_id: string;
  name: string;
  facility_type: string;
  status: string;
  source?: string;
}

// --- Typed GeoJSON Feature and FeatureCollection aliases ---
// Roads and bike lanes can be MultiLineString in the full Eugene cache when
// the city's GIS export splits a segment at intersections.

export type RoadFeature = Feature<
  RoadProperties,
  LineStringGeometry | MultiLineStringGeometry
>;
export type CurbRampFeature = Feature<CurbRampProperties, PointGeometry>;
export type HydrantFeature = Feature<HydrantProperties, PointGeometry>;
export type BikeLaneFeature = Feature<
  BikeLaneProperties,
  LineStringGeometry | MultiLineStringGeometry
>;

export type RoadFeatureCollection = FeatureCollection<RoadFeature>;
export type CurbRampFeatureCollection = FeatureCollection<CurbRampFeature>;
export type HydrantFeatureCollection = FeatureCollection<HydrantFeature>;
export type BikeLaneFeatureCollection = FeatureCollection<BikeLaneFeature>;

export interface LayerOption {
  id: LayerId;
  label: string;
  disabled?: boolean;
}

export type LayerVisibility = Record<LayerId, boolean>;

// LAYER_OPTIONS drives both the LayerPanel checkbox list and the order in
// which layers are described in the UI.  Changing the order here reorders
// the panel without touching the component.
export const LAYER_OPTIONS: LayerOption[] = [
  { id: "roads", label: "Roads" },
  { id: "sidewalkRamps", label: "Sidewalk ramps" },
  { id: "hydrants", label: "Fire hydrants" },
  { id: "bikeLanes", label: "Bike lanes" },
  { id: "annotations", label: "User annotations" }
];

// All layers are visible by default so the map is populated on first load.
export const DEFAULT_LAYER_VISIBILITY: LayerVisibility = {
  roads: true,
  sidewalkRamps: true,
  hydrants: true,
  annotations: true,
  bikeLanes: true
};
