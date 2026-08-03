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
  measurements?: string[];
  fieldReviewPrompts?: string[];
  screeningDisclaimer?: string;
  coordinates: Position;
}

const MINIMUM_RAMP_WIDTH_FEET = 4;
const MAXIMUM_RAMP_GRADE_PERCENT = 8.33;
const MAXIMUM_CROSS_SLOPE_PERCENT = 2.08;

export const CURB_RAMP_SCREENING_DISCLAIMER =
  "Screening only: published measurements are field-review prompts, not an accessibility-compliance finding. Verify measurement method, site geometry, exceptions, alterations, and applicable requirements.";

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
  const measurements = [
    formatMeasurement("Width", properties.width_feet, "ft"),
    formatMeasurement("Left width", properties.left_width_feet, "ft"),
    formatMeasurement("Right width", properties.right_width_feet, "ft"),
    formatMeasurement("Grade", properties.grade_percent, "%"),
    formatMeasurement("Left grade", properties.left_grade_percent, "%"),
    formatMeasurement("Right grade", properties.right_grade_percent, "%"),
    formatMeasurement("Cross slope", properties.cross_slope_percent, "%"),
    formatMeasurement("Left cross slope", properties.left_cross_slope_percent, "%"),
    formatMeasurement("Right cross slope", properties.right_cross_slope_percent, "%")
  ].filter((measurement): measurement is string => measurement !== null);
  const fieldReviewPrompts = getCurbRampFieldReviewPrompts(properties);

  return {
    id: properties.ramp_id,
    layerId: "sidewalkRamps",
    title: properties.ramp_id,
    subtitle: "Sidewalk ramp",
    source: properties.source ?? "City of Eugene GIS",
    status: properties.status,
    notes: `Condition: ${properties.condition}; configuration: ${
      properties.configuration ?? "unknown"
    }`,
    measurements,
    fieldReviewPrompts,
    screeningDisclaimer: measurements.length
      ? CURB_RAMP_SCREENING_DISCLAIMER
      : undefined,
    coordinates: getFeatureCenter(geometry)
  };
}

function formatMeasurement(
  label: string,
  value: number | null | undefined,
  unit: string
): string | null {
  const isPhysicalWidth = unit === "ft";
  return typeof value === "number" &&
    Number.isFinite(value) &&
    (!isPhysicalWidth || value > 0)
    ? `${label}: ${value} ${unit}`
    : null;
}

/** Compare published ramp values with documented dimensional references.
 *
 * The result is intentionally phrased as a field-review prompt. CURBO does
 * not know the measurement method, site geometry, exceptions, alteration
 * history, or governing requirements needed for a compliance determination.
 */
export function getCurbRampFieldReviewPrompts(
  properties: CurbRampProperties
): string[] {
  const prompts: string[] = [];
  const widthMeasurements: Array<[string, number | null | undefined]> = [
    ["Width", properties.width_feet],
    ["Left width", properties.left_width_feet],
    ["Right width", properties.right_width_feet]
  ];
  const gradeMeasurements: Array<[string, number | null | undefined]> = [
    ["Grade", properties.grade_percent],
    ["Left grade", properties.left_grade_percent],
    ["Right grade", properties.right_grade_percent]
  ];
  const crossSlopeMeasurements: Array<[string, number | null | undefined]> = [
    ["Cross slope", properties.cross_slope_percent],
    ["Left cross slope", properties.left_cross_slope_percent],
    ["Right cross slope", properties.right_cross_slope_percent]
  ];

  widthMeasurements.forEach(([label, value]) => {
    if (isFiniteMeasurement(value) && value > 0 && value < MINIMUM_RAMP_WIDTH_FEET) {
      prompts.push(
        `${label} ${value} ft is below the ${MINIMUM_RAMP_WIDTH_FEET} ft field-review reference.`
      );
    }
  });
  gradeMeasurements.forEach(([label, value]) => {
    if (isFiniteMeasurement(value) && value > MAXIMUM_RAMP_GRADE_PERCENT) {
      prompts.push(
        `${label} ${value}% exceeds the ${MAXIMUM_RAMP_GRADE_PERCENT}% field-review reference.`
      );
    }
  });
  crossSlopeMeasurements.forEach(([label, value]) => {
    if (isFiniteMeasurement(value) && value > MAXIMUM_CROSS_SLOPE_PERCENT) {
      prompts.push(
        `${label} ${value}% exceeds the ${MAXIMUM_CROSS_SLOPE_PERCENT}% field-review reference.`
      );
    }
  });
  return prompts;
}

function isFiniteMeasurement(
  value: number | null | undefined
): value is number {
  return typeof value === "number" && Number.isFinite(value);
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
