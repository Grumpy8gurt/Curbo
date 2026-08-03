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

export async function getAnnotations(): Promise<AnnotationFeatureCollection> {
  // getFallbackAnnotations is passed as a factory function (not called here)
  // so the fallback data reflects any annotations added during the session.
  return fetchJsonWithFallback("/api/annotations", getFallbackAnnotations);
}

export async function createAnnotation(
  annotation: AnnotationDraft
): Promise<AnnotationFeature> {
  return fetchJsonWithFallback("/api/annotations", () => addFallbackAnnotation(annotation), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    // The backend schema accepts camelCase via AliasChoices, so annotationType
    // is sent as-is from the frontend draft object.
    body: JSON.stringify({
      annotationType: annotation.annotationType,
      description: annotation.description,
      geometry: annotation.geometry,
      source: "frontend"
    })
  });
}

export async function updateAnnotationStatus(
  annotationId: string,
  status: AnnotationStatus
): Promise<AnnotationFeature> {
  return fetchJsonWithFallback(
    `/api/annotations/${encodeURIComponent(annotationId)}`,
    () => updateFallbackAnnotation(annotationId, status),
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ status })
    }
  );
}
