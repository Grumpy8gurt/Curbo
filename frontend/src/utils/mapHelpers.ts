import type {
  AnnotationFeature,
  AnnotationProperties
} from "../types/annotations";
import type { Feature, Geometry, LineStringGeometry, Position } from "../types/geojson";
import type {
  BikeLaneProperties,
  CurbRampProperties,
  HydrantProperties,
  LayerId,
  RoadFeature,
  RoadProperties
} from "../types/layers";

/**
 * Normalised view of a selected map feature used across the FeaturePopup
 * and App state.  Decouples the popup from knowing the internal shape of each
 * layer's properties object.
 */
export interface SelectedFeatureDetails {
  id: string;
  layerId: LayerId;
  title: string;
  subtitle: string;
  source: string;
  status?: string;
  notes?: string;
  geometryLabel?: string;
  coordinates: Position;
}

/**
 * Return the visual centre of a geometry for fly-to and popup placement.
 *
 * - Point:            returns the coordinate directly.
 * - LineString:       returns the midpoint vertex (index floor(n/2)).
 * - MultiLineString:  picks the middle line, then its midpoint vertex.
 * - Fallback:         first coordinate of the first ring (Polygon).
 *
 * Using a vertex rather than a computed centroid is fast and sufficient for
 * the short road segments in the Eugene dataset.
 */
export function getFeatureCenter(geometry: Geometry): Position {
  if (geometry.type === "Point") {
    return geometry.coordinates;
  }

  if (geometry.type === "LineString") {
    return geometry.coordinates[Math.floor(geometry.coordinates.length / 2)];
  }

  if (geometry.type === "MultiLineString") {
    const line = geometry.coordinates[Math.floor(geometry.coordinates.length / 2)];
    return line[Math.floor(line.length / 2)];
  }

  return geometry.coordinates[0][0];
}

/**
 * Format a road feature as a human-readable dropdown label.
 * Example: "Willamette Street (arterial)"
 */
export function getRoadOptionLabel(feature: RoadFeature): string {
  return `${feature.properties.name} (${feature.properties.classification})`;
}

/**
 * Map a raw GeoJSON Feature (from a MapLibre click event) to a
 * SelectedFeatureDetails object based on which layer it came from.
 *
 * The `as unknown as X` casts are required because MapLibre's feature.toJSON()
 * returns a plain object typed as Feature rather than our typed subtypes.
 */
export function toSelectedFeatureDetails(
  layerId: LayerId,
  feature: Feature
): SelectedFeatureDetails {
  switch (layerId) {
    case "roads":
      return fromRoadFeature(feature as unknown as RoadFeature);
    case "sidewalkRamps":
      return fromCurbRampFeature(
        feature.properties as unknown as CurbRampProperties,
        feature.geometry
      );
    case "hydrants":
      return fromHydrantFeature(
        feature.properties as unknown as HydrantProperties,
        feature.geometry
      );
    case "bikeLanes":
      return fromBikeLaneFeature(
        feature.properties as unknown as BikeLaneProperties,
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
    layerId: "sidewalkRamps",
    title: properties.ramp_id,
    subtitle: "Sidewalk ramp",
    source: properties.source ?? "City of Eugene GIS",
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
    source: properties.source ?? "City of Eugene GIS",
    notes: `Flow class: ${properties.flow_class}`,
    coordinates: getFeatureCenter(geometry)
  };
}

function fromBikeLaneFeature(
  properties: BikeLaneProperties,
  geometry: Geometry
): SelectedFeatureDetails {
  return {
    id: properties.bike_lane_id,
    layerId: "bikeLanes",
    title: properties.name,
    subtitle: properties.facility_type,
    source: properties.source ?? "City of Eugene GIS",
    status: properties.status,
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
    geometryLabel:
      feature.geometry.type === "LineString"
        ? `Line note (${feature.geometry.coordinates.length} vertices)`
        : "Point note",
    coordinates: getFeatureCenter(feature.geometry)
  };
}

/** Type predicate: returns true when the geometry is a plain LineString. */
export function isRoadGeometry(geometry: Geometry): geometry is LineStringGeometry {
  return geometry.type === "LineString";
}
