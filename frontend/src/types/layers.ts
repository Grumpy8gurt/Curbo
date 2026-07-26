import type {
  Feature,
  FeatureCollection,
  LineStringGeometry,
  PointGeometry
} from "./geojson";

export type LayerId =
  | "roads"
  | "curbRamps"
  | "hydrants"
  | "annotations"
  | "bikeLanes"
  | "busStops"
  | "parkingZones"
  | "parcels";

export interface RoadProperties {
  road_id: string;
  name: string;
  classification: string;
}

export interface CurbRampProperties {
  ramp_id: string;
  status: string;
  condition: string;
}

export interface HydrantProperties {
  hydrant_id: string;
  flow_class: string;
}

export interface PlaceholderProperties {
  id: string;
  name: string;
}

export type RoadFeature = Feature<RoadProperties, LineStringGeometry>;
export type CurbRampFeature = Feature<CurbRampProperties, PointGeometry>;
export type HydrantFeature = Feature<HydrantProperties, PointGeometry>;
export type PlaceholderFeature = Feature<PlaceholderProperties, PointGeometry>;

export type RoadFeatureCollection = FeatureCollection<RoadFeature>;
export type CurbRampFeatureCollection = FeatureCollection<CurbRampFeature>;
export type HydrantFeatureCollection = FeatureCollection<HydrantFeature>;
export type PlaceholderFeatureCollection = FeatureCollection<PlaceholderFeature>;

export interface LayerOption {
  id: LayerId;
  label: string;
  disabled?: boolean;
}

export type LayerVisibility = Record<LayerId, boolean>;

export const LAYER_OPTIONS: LayerOption[] = [
  { id: "roads", label: "Roads" },
  { id: "curbRamps", label: "Curb ramps" },
  { id: "hydrants", label: "Hydrants" },
  { id: "annotations", label: "Annotations" },
  { id: "bikeLanes", label: "Bike lanes", disabled: true },
  { id: "busStops", label: "Bus stops", disabled: true },
  { id: "parkingZones", label: "Parking zones", disabled: true },
  { id: "parcels", label: "Parcels", disabled: true }
];

export const DEFAULT_LAYER_VISIBILITY: LayerVisibility = {
  roads: true,
  curbRamps: true,
  hydrants: true,
  annotations: true,
  bikeLanes: false,
  busStops: false,
  parkingZones: false,
  parcels: false
};
