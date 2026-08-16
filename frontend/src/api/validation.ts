import type { AnnotationFeature, AnnotationFeatureCollection } from "../types/annotations";
import type { CorridorSummary } from "../types/corridors";
import type { FeatureCollection } from "../types/geojson";
import type {
  BikeLaneFeatureCollection,
  CurbRampFeatureCollection,
  HydrantFeatureCollection,
  RoadFeatureCollection
} from "../types/layers";
import type { CorridorReportResult } from "../types/reports";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isFeatureCollection(value: unknown): value is FeatureCollection {
  return (
    isRecord(value) &&
    value.type === "FeatureCollection" &&
    Array.isArray(value.features)
  );
}

function hasProperties(value: unknown, names: string[]): boolean {
  if (!isRecord(value) || value.type !== "Feature" || !isRecord(value.properties)) {
    return false;
  }
  const properties = value.properties;
  return names.every((name) => typeof properties[name] === "string");
}

export function isRoadFeatureCollection(value: unknown): value is RoadFeatureCollection {
  return (
    isFeatureCollection(value) &&
    value.features.every((feature) =>
      hasProperties(feature, ["road_id", "name", "classification"])
    )
  );
}

export function isCurbRampFeatureCollection(
  value: unknown
): value is CurbRampFeatureCollection {
  return (
    isFeatureCollection(value) &&
    value.features.every((feature) =>
      hasProperties(feature, ["ramp_id", "status", "condition"])
    )
  );
}

export function isHydrantFeatureCollection(
  value: unknown
): value is HydrantFeatureCollection {
  return (
    isFeatureCollection(value) &&
    value.features.every((feature) =>
      hasProperties(feature, ["hydrant_id", "flow_class"])
    )
  );
}

export function isBikeLaneFeatureCollection(
  value: unknown
): value is BikeLaneFeatureCollection {
  return (
    isFeatureCollection(value) &&
    value.features.every((feature) =>
      hasProperties(feature, ["bike_lane_id", "name", "facility_type", "status"])
    )
  );
}

export function isAnnotationFeature(value: unknown): value is AnnotationFeature {
  if (!isRecord(value) || value.type !== "Feature" || !isRecord(value.properties)) {
    return false;
  }
  const properties = value.properties;
  return (
    typeof value.id === "string" &&
    isRecord(value.geometry) &&
    typeof properties.annotation_id === "string" &&
    typeof properties.annotation_type === "string" &&
    typeof properties.description === "string" &&
    typeof properties.status === "string" &&
    typeof properties.source === "string" &&
    typeof properties.created_at === "string" &&
    typeof properties.version === "number"
  );
}

export function isAnnotationFeatureCollection(
  value: unknown
): value is AnnotationFeatureCollection {
  return isFeatureCollection(value) && value.features.every(isAnnotationFeature);
}

export function isCorridorSummary(value: unknown): value is CorridorSummary {
  return (
    isRecord(value) &&
    typeof value.corridorId === "string" &&
    typeof value.roadId === "string" &&
    typeof value.name === "string" &&
    typeof value.reviewPriority === "string" &&
    Array.isArray(value.reviewSignals) &&
    typeof value.dataLimitation === "string" &&
    Array.isArray(value.planningNotes)
  );
}

export function isCorridorReportResult(value: unknown): value is CorridorReportResult {
  return (
    isRecord(value) &&
    typeof value.reportId === "string" &&
    typeof value.roadId === "string" &&
    typeof value.downloadUrl === "string" &&
    typeof value.summary === "string"
  );
}
