import type {
  AnnotationFeature,
  AnnotationProperties
} from "../types/annotations";
import type { Feature, Geometry, LineStringGeometry, Position } from "../types/geojson";
import type {
  CurbRampProperties,
  HydrantProperties,
  LayerId,
  RoadFeature,
  RoadProperties
} from "../types/layers";

export interface SelectedFeatureDetails {
  id: string;
  layerId: LayerId;
  title: string;
  subtitle: string;
  source: string;
  status?: string;
  notes?: string;
  coordinates: Position;
}

export function getFeatureCenter(geometry: Geometry): Position {
  if (geometry.type === "Point") {
    return geometry.coordinates;
  }

  if (geometry.type === "LineString") {
    return geometry.coordinates[Math.floor(geometry.coordinates.length / 2)];
  }

  return geometry.coordinates[0][0];
}

export function getRoadOptionLabel(feature: RoadFeature): string {
  return `${feature.properties.name} (${feature.properties.classification})`;
}

export function toSelectedFeatureDetails(
  layerId: LayerId,
  feature: Feature
): SelectedFeatureDetails {
  switch (layerId) {
    case "roads":
      return fromRoadFeature(feature as unknown as RoadFeature);
    case "curbRamps":
      return fromCurbRampFeature(
        feature.properties as unknown as CurbRampProperties,
        feature.geometry
      );
    case "hydrants":
      return fromHydrantFeature(
        feature.properties as unknown as HydrantProperties,
        feature.geometry
      );
    case "annotations":
      return fromAnnotationFeature(feature as unknown as AnnotationFeature);
    default:
      return {
        id: String(feature.id ?? "unknown"),
        layerId,
        title: "Map feature",
        subtitle: "Unconfigured layer",
        source: "frontend",
        coordinates: getFeatureCenter(feature.geometry)
      };
  }
}

function fromRoadFeature(feature: RoadFeature): SelectedFeatureDetails {
  const properties = feature.properties as RoadProperties;

  return {
    id: properties.road_id,
    layerId: "roads",
    title: properties.name,
    subtitle: properties.classification,
    source: "roads layer",
    coordinates: getFeatureCenter(feature.geometry)
  };
}

function fromCurbRampFeature(
  properties: CurbRampProperties,
  geometry: Geometry
): SelectedFeatureDetails {
  return {
    id: properties.ramp_id,
    layerId: "curbRamps",
    title: properties.ramp_id,
    subtitle: "Curb ramp",
    source: "curb ramps layer",
    status: properties.status,
    notes: `Condition: ${properties.condition}`,
    coordinates: getFeatureCenter(geometry)
  };
}

function fromHydrantFeature(
  properties: HydrantProperties,
  geometry: Geometry
): SelectedFeatureDetails {
  return {
    id: properties.hydrant_id,
    layerId: "hydrants",
    title: properties.hydrant_id,
    subtitle: "Hydrant",
    source: "hydrants layer",
    notes: `Flow class: ${properties.flow_class}`,
    coordinates: getFeatureCenter(geometry)
  };
}

function fromAnnotationFeature(feature: AnnotationFeature): SelectedFeatureDetails {
  const properties = feature.properties as AnnotationProperties;

  return {
    id: properties.annotation_id,
    layerId: "annotations",
    title: properties.annotation_type,
    subtitle: "Planner annotation",
    source: properties.source,
    status: properties.status,
    notes: properties.description,
    coordinates: getFeatureCenter(feature.geometry)
  };
}

export function isRoadGeometry(geometry: Geometry): geometry is LineStringGeometry {
  return geometry.type === "LineString";
}
