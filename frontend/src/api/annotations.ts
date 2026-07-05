import { apiUrl, resolveMock, USE_MOCK_API } from "./client";
import { addMockAnnotation, getMockAnnotations } from "./mockData";
import type {
  AnnotationDraft,
  AnnotationFeature,
  AnnotationFeatureCollection
} from "../types/annotations";

export async function getAnnotations(): Promise<AnnotationFeatureCollection> {
  if (USE_MOCK_API) {
    return resolveMock(getMockAnnotations());
  }

  const response = await fetch(apiUrl("/api/annotations"));
  return response.json();
}

export async function createAnnotation(
  annotation: AnnotationDraft
): Promise<AnnotationFeature> {
  if (USE_MOCK_API) {
    return resolveMock(addMockAnnotation(annotation));
  }

  const response = await fetch(apiUrl("/api/annotations"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(annotation)
  });

  return response.json();
}
