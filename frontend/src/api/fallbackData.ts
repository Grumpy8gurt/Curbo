/**
 * fallbackData.ts
 *
 * In-memory offline dataset used when the backend is unavailable or when
 * VITE_USE_MOCK_API=true.  All coordinates are in the Eugene, OR area.
 *
 * Note: annotations is module-level mutable state so that addFallbackAnnotation
 * can persist new annotations across multiple API calls within the same session.
 * This is intentionally lightweight — the backend provides true persistence.
 */
import type {
  AnnotationDraft,
  AnnotationFeature,
  AnnotationFeatureCollection
} from "../types/annotations";
import type { CorridorSummary } from "../types/corridors";
import type { Position } from "../types/geojson";
import type {
  BikeLaneFeatureCollection,
  CurbRampFeatureCollection,
  HydrantFeatureCollection,
  RoadFeatureCollection
} from "../types/layers";
import type { CorridorReportResult } from "../types/reports";

const roads: RoadFeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: {
        road_id: "road_rd_001",
        name: "Willamette Street",
        classification: "arterial"
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [-123.0935, 44.0508],
          [-123.0912, 44.0516],
          [-123.0884, 44.0528]
        ]
      }
    },
    {
      type: "Feature",
      properties: {
        road_id: "road_rd_002",
        name: "East 11th Avenue",
        classification: "collector"
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [-123.0927, 44.0489],
          [-123.0899, 44.049],
          [-123.0867, 44.0491]
        ]
      }
    }
  ]
};

const curbRamps: CurbRampFeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: {
        ramp_id: "cr_001",
        status: "existing",
        condition: "good"
      },
      geometry: {
        type: "Point",
        coordinates: [-123.0914, 44.0514]
      }
    },
    {
      type: "Feature",
      properties: {
        ramp_id: "cr_002",
        status: "needs_review",
        condition: "unknown"
      },
      geometry: {
        type: "Point",
        coordinates: [-123.0888, 44.0526]
      }
    },
    {
      type: "Feature",
      properties: {
        ramp_id: "cr_003",
        status: "existing",
        condition: "fair"
      },
      geometry: {
        type: "Point",
        coordinates: [-123.087, 44.0492]
      }
    }
  ]
};

const hydrants: HydrantFeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: {
        hydrant_id: "hy_001",
        flow_class: "standard"
      },
      geometry: {
        type: "Point",
        coordinates: [-123.0903, 44.0511]
      }
    },
    {
      type: "Feature",
      properties: {
        hydrant_id: "hy_002",
        flow_class: "high"
      },
      geometry: {
        type: "Point",
        coordinates: [-123.0878, 44.0494]
      }
    }
  ]
};

const bikeLanes: BikeLaneFeatureCollection = {
  type: "FeatureCollection",
  metadata: { status: "sample-fallback", source: "CURBO local fallback" },
  features: [
    {
      type: "Feature",
      properties: {
        bike_lane_id: "bike_demo_001",
        name: "East 11th Avenue",
        facility_type: "Bike lane",
        status: "Built"
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [-123.0927, 44.0489],
          [-123.0899, 44.049],
          [-123.0867, 44.0491]
        ]
      }
    }
  ]
};

let annotationCounter = 3;
let reportCounter = 0;

// Module-level mutable collection — starts with two seed annotations matching
// the backend defaults so the UI looks consistent whether connected or not.
let annotations: AnnotationFeatureCollection = {
  type: "FeatureCollection",
  metadata: { status: "local fallback", source: "CURBO in-memory fallback" },
  features: [
    createAnnotationFeature({
      annotationType: "missing curb cut",
      description: "Northwest corner slope feels absent during field review.",
      geometry: {
        type: "Point",
        coordinates: [-123.0894, 44.0519]
      }
    }, "ann_001", "2026-07-05T15:00:00Z"),
    createAnnotationFeature({
      annotationType: "obstruction",
      description: "Temporary sign blocks ramp access near the curb return.",
      geometry: {
        type: "Point",
        coordinates: [-123.0874, 44.0493]
      }
    }, "ann_002", "2026-07-05T15:10:00Z")
  ]
};

const corridorSummaries: Record<string, CorridorSummary> = {
  road_rd_001: {
    corridorId: "cor_road_rd_001",
    roadId: "road_rd_001",
    name: "Willamette Street",
    knownCurbRamps: 8,
    possibleMissingCurbCuts: 2,
    hydrantsNearby: 4,
    bikeLanesNearby: 1,
    userAnnotationsNearby: 1,
    busStopsNearby: 1,
    parkingConflicts: 7,
    bikeLaneFeasibility: "Medium",
    planningNotes: [
      "Downtown pedestrian demand is high near the mid-block crossings.",
      "A loading zone may conflict with future ramp reconstruction."
    ]
  },
  road_rd_002: {
    corridorId: "cor_road_rd_002",
    roadId: "road_rd_002",
    name: "East 11th Avenue",
    knownCurbRamps: 5,
    possibleMissingCurbCuts: 1,
    hydrantsNearby: 2,
    bikeLanesNearby: 1,
    userAnnotationsNearby: 1,
    busStopsNearby: 1,
    parkingConflicts: 3,
    bikeLaneFeasibility: "High",
    planningNotes: [
      "Existing cross section leaves room for ADA improvements.",
      "Transit stop spacing suggests one corner deserves priority review."
    ]
  }
};

function createAnnotationFeature(
  draft: AnnotationDraft,
  annotationId = `ann_${String(++annotationCounter).padStart(3, "0")}`,
  createdAt = new Date().toISOString()
): AnnotationFeature {
  return {
    type: "Feature",
    id: annotationId,
    properties: {
      annotation_id: annotationId,
      annotation_type: draft.annotationType,
      description: draft.description,
      status: "pending",
      source: "planner",
      created_at: createdAt
    },
    geometry: draft.geometry
  };
}

export function getFallbackRoads(): RoadFeatureCollection {
  return roads;
}

export function getFallbackSidewalkRamps(): CurbRampFeatureCollection {
  return curbRamps;
}

export function getFallbackHydrants(): HydrantFeatureCollection {
  return hydrants;
}

export function getFallbackAnnotations(): AnnotationFeatureCollection {
  return annotations;
}

export function getFallbackBikeLanes(): BikeLaneFeatureCollection {
  return bikeLanes;
}

export function addFallbackAnnotation(draft: AnnotationDraft): AnnotationFeature {
  const feature = createAnnotationFeature(draft);
  annotations = {
    ...annotations,
    features: [...annotations.features, feature]
  };
  return feature;
}

export function getFallbackCorridorSummary(roadId: string): CorridorSummary {
  // Return a pre-defined summary for known demo roads or a zeroed placeholder
  // for any other road ID so the UI degrades gracefully.
  return (
    corridorSummaries[roadId] ?? {
      corridorId: `cor_${roadId}`,
      roadId,
      name: "Unknown corridor",
      knownCurbRamps: 0,
      possibleMissingCurbCuts: 0,
      hydrantsNearby: 0,
      bikeLanesNearby: 0,
      userAnnotationsNearby: 0,
      busStopsNearby: 0,
      parkingConflicts: 0,
      bikeLaneFeasibility: "Low",
      planningNotes: ["No fallback corridor summary is defined for this road yet."]
    }
  );
}

export function createFallbackReport(corridorId: string, roadName: string): CorridorReportResult {
  reportCounter += 1;
  const reportId = `rep_${String(reportCounter).padStart(3, "0")}`;
  return {
    reportId,
    roadId: corridorId,
    downloadUrl: "",
    summary: `${roadName} report preview generated locally. Connect the backend to download HTML.`
  };
}
