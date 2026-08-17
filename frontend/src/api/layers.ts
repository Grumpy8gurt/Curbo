import { fetchJsonWithFallback } from "./client";
import {
  getFallbackBikeLanes,
  getFallbackHydrants,
  getFallbackRoads,
  getFallbackSidewalkRamps
} from "./fallbackData";
import type {
  BikeLaneFeatureCollection,
  CurbRampFeatureCollection,
  HydrantFeatureCollection,
  RoadFeatureCollection
} from "../types/layers";
import {
  isBikeLaneFeatureCollection,
  isCurbRampFeatureCollection,
  isHydrantFeatureCollection,
  isRoadFeatureCollection
} from "./validation";

// Each getter passes a pre-computed fallback value (not a factory function)
// because the fallback collections are module-level constants and are safe to
// share directly.  fetchJsonWithFallback deep-clones them before returning.
export async function getRoads(): Promise<RoadFeatureCollection> {
  return fetchJsonWithFallback(
    "/api/v1/layers/roads",
    getFallbackRoads(),
    // Chrome can revalidate this large response with a bodyless 304 response.
    // Always request a complete payload so a page refresh cannot empty the map.
    { cache: "no-store" },
    isRoadFeatureCollection
  );
}

export async function getSidewalkRamps(): Promise<CurbRampFeatureCollection> {
  return fetchJsonWithFallback(
    "/api/v1/layers/sidewalk-ramps",
    getFallbackSidewalkRamps(),
    undefined,
    isCurbRampFeatureCollection
  );
}

export async function getHydrants(): Promise<HydrantFeatureCollection> {
  return fetchJsonWithFallback(
    "/api/v1/layers/hydrants",
    getFallbackHydrants(),
    undefined,
    isHydrantFeatureCollection
  );
}

export async function getBikeLanes(): Promise<BikeLaneFeatureCollection> {
  return fetchJsonWithFallback(
    "/api/v1/layers/bike-lanes",
    getFallbackBikeLanes(),
    undefined,
    isBikeLaneFeatureCollection
  );
}
