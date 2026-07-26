import { fetchJsonWithFallback } from "./client";
import { addFallbackAnnotation, getFallbackAnnotations } from "./fallbackData";
import type {
  AnnotationDraft,
  AnnotationFeature,
  AnnotationFeatureCollection
} from "../types/annotations";

export async function getAnnotations(): Promise<AnnotationFeatureCollection> {
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
    body: JSON.stringify({
      annotationType: annotation.annotationType,
      description: annotation.description,
      latitude: annotation.latitude,
      longitude: annotation.longitude,
      source: "frontend"
    })
  });
}
