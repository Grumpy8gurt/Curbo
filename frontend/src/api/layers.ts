import { apiUrl, resolveMock, USE_MOCK_API } from "./client";
import {
  getMockCurbRamps,
  getMockDetections,
  getMockHydrants,
  getMockPlaceholderLayer,
  getMockRoads
} from "./mockData";
import type {
  CurbRampFeatureCollection,
  HydrantFeatureCollection,
  PlaceholderFeatureCollection,
  RoadFeatureCollection
} from "../types/layers";
import type { DetectionFeatureCollection } from "../types/detections";

export async function getRoads(): Promise<RoadFeatureCollection> {
  if (USE_MOCK_API) {
    return resolveMock(getMockRoads());
  }

  const response = await fetch(apiUrl("/api/layers/roads"));
  return response.json();
}

export async function getCurbRamps(): Promise<CurbRampFeatureCollection> {
  if (USE_MOCK_API) {
    return resolveMock(getMockCurbRamps());
  }

  const response = await fetch(apiUrl("/api/layers/curb-ramps"));
  return response.json();
}

export async function getHydrants(): Promise<HydrantFeatureCollection> {
  if (USE_MOCK_API) {
    return resolveMock(getMockHydrants());
  }

  const response = await fetch(apiUrl("/api/layers/hydrants"));
  return response.json();
}

export async function getDetections(): Promise<DetectionFeatureCollection> {
  if (USE_MOCK_API) {
    return resolveMock(getMockDetections());
  }

  const response = await fetch(apiUrl("/api/layers/detections"));
  const payload = await response.json();

  return {
    type: "FeatureCollection",
    features: payload.features.map((feature: any) => ({
      ...feature,
      properties: {
        detection_id: feature.properties.detection_id ?? feature.properties.id,
        label: feature.properties.label,
        confidence: feature.properties.confidence,
        review_status: feature.properties.review_status,
        upload_id: feature.properties.upload_id ?? feature.properties.image_id,
        source: feature.properties.source ?? "backend"
      }
    }))
  };
}

export async function getPlaceholderLayer(): Promise<PlaceholderFeatureCollection> {
  return resolveMock(getMockPlaceholderLayer(), 40);
}
