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
