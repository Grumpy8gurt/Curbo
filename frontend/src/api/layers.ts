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

// Each getter passes a pre-computed fallback value (not a factory function)
// because the fallback collections are module-level constants and are safe to
// share directly.  fetchJsonWithFallback deep-clones them before returning.
export async function getRoads(): Promise<RoadFeatureCollection> {
  return fetchJsonWithFallback("/api/layers/roads", getFallbackRoads());
}

export async function getSidewalkRamps(): Promise<CurbRampFeatureCollection> {
  return fetchJsonWithFallback(
    "/api/layers/sidewalk-ramps",
    getFallbackSidewalkRamps()
  );
}

export async function getHydrants(): Promise<HydrantFeatureCollection> {
  return fetchJsonWithFallback("/api/layers/hydrants", getFallbackHydrants());
}

export async function getBikeLanes(): Promise<BikeLaneFeatureCollection> {
  return fetchJsonWithFallback("/api/layers/bike-lanes", getFallbackBikeLanes());
}
