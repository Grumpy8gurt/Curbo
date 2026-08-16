import { fetchJsonWithFallback } from "./client";
import {
  addFallbackAnnotation,
  getFallbackAnnotations,
  updateFallbackAnnotation
} from "./fallbackData";
import type {
  AnnotationDraft,
  AnnotationFeature,
  AnnotationFeatureCollection,
  AnnotationStatus
} from "../types/annotations";
import { isAnnotationFeature, isAnnotationFeatureCollection } from "./validation";

export async function getAnnotations(): Promise<AnnotationFeatureCollection> {
  // getFallbackAnnotations is passed as a factory function (not called here)
  // so the fallback data reflects any annotations added during the session.
  return fetchJsonWithFallback(
    "/api/v1/annotations",
    getFallbackAnnotations,
    undefined,
    isAnnotationFeatureCollection
  );
}

export async function createAnnotation(
  annotation: AnnotationDraft
): Promise<AnnotationFeature> {
  return fetchJsonWithFallback(
    "/api/v1/annotations",
    () => addFallbackAnnotation(annotation),
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": createIdempotencyKey()
      },
      body: JSON.stringify({
        annotationType: annotation.annotationType,
        description: annotation.description,
        geometry: annotation.geometry
      })
    },
    isAnnotationFeature
  );
}

function createIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `curbo-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export async function updateAnnotationStatus(
  annotationId: string,
  status: AnnotationStatus,
  expectedVersion: number
): Promise<AnnotationFeature> {
  return fetchJsonWithFallback(
    `/api/v1/annotations/${encodeURIComponent(annotationId)}`,
    () => updateFallbackAnnotation(annotationId, status),
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ status, expectedVersion })
    },
    isAnnotationFeature
  );
}
