import type {
  AnnotationDraft,
  AnnotationFeature,
  AnnotationFeatureCollection
} from "../types/annotations";
import type { CorridorSummary } from "../types/corridors";
import type { Position } from "../types/geojson";
import type {
  CurbRampFeatureCollection,
  HydrantFeatureCollection,
  PlaceholderFeatureCollection,
  RoadFeatureCollection
} from "../types/layers";
import type { CorridorReportResult } from "../types/reports";

const roads: RoadFeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: {
        road_id: "rd_001",
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
        road_id: "rd_002",
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

const emptyPoints = (): PlaceholderFeatureCollection => ({
  type: "FeatureCollection",
  features: []
});

let annotationCounter = 3;
let reportCounter = 0;

let annotations: AnnotationFeatureCollection = {
  type: "FeatureCollection",
  features: [
    createAnnotationFeature({
      annotationType: "missing curb cut",
      description: "Northwest corner slope feels absent during field review.",
      latitude: 44.0519,
      longitude: -123.0894
    }, "ann_001", "2026-07-05T15:00:00Z"),
    createAnnotationFeature({
      annotationType: "obstruction",
      description: "Temporary sign blocks ramp access near the curb return.",
      latitude: 44.0493,
      longitude: -123.0874
    }, "ann_002", "2026-07-05T15:10:00Z")
  ]
};

const corridorSummaries: Record<string, CorridorSummary> = {
  rd_001: {
    corridorId: "cor_rd_001",
    roadId: "rd_001",
    name: "Willamette Street",
    knownCurbRamps: 8,
    possibleMissingCurbCuts: 2,
    hydrantsNearby: 4,
    busStopsNearby: 1,
    parkingConflicts: 7,
    bikeLaneFeasibility: "Medium",
    planningNotes: [
      "Downtown pedestrian demand is high near the mid-block crossings.",
      "A loading zone may conflict with future ramp reconstruction."
    ]
  },
  rd_002: {
    corridorId: "cor_rd_002",
    roadId: "rd_002",
    name: "East 11th Avenue",
    knownCurbRamps: 5,
    possibleMissingCurbCuts: 1,
    hydrantsNearby: 2,
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
    geometry: {
      type: "Point",
      coordinates: [draft.longitude, draft.latitude]
    }
  };
}

export function getMockRoads(): RoadFeatureCollection {
  return roads;
}

export function getMockCurbRamps(): CurbRampFeatureCollection {
  return curbRamps;
}

export function getMockHydrants(): HydrantFeatureCollection {
  return hydrants;
}

export function getMockAnnotations(): AnnotationFeatureCollection {
  return annotations;
}

export function getMockPlaceholderLayer(): PlaceholderFeatureCollection {
  return emptyPoints();
}

export function addMockAnnotation(draft: AnnotationDraft): AnnotationFeature {
  const feature = createAnnotationFeature(draft);
  annotations = {
    ...annotations,
    features: [...annotations.features, feature]
  };
  return feature;
}

export function getMockCorridorSummary(roadId: string): CorridorSummary {
  return (
    corridorSummaries[roadId] ?? {
      corridorId: `cor_${roadId}`,
      roadId,
      name: "Unknown corridor",
      knownCurbRamps: 0,
      possibleMissingCurbCuts: 0,
      hydrantsNearby: 0,
      busStopsNearby: 0,
      parkingConflicts: 0,
      bikeLaneFeasibility: "Low",
      planningNotes: ["No mock corridor summary is defined for this road yet."]
    }
  );
}

export function createMockReport(corridorId: string, roadName: string): CorridorReportResult {
  reportCounter += 1;
  const reportId = `rep_${String(reportCounter).padStart(3, "0")}`;
  return {
    reportId,
    roadId: corridorId,
    downloadUrl: `/api/reports/${reportId}/download`,
    summary: `${roadName} corridor report queued successfully. Mock export includes counts and planning notes.`
  };
}
