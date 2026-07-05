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
  const payload = await response.json();

  if (payload.type === "FeatureCollection") {
    return payload;
  }

  return {
    type: "FeatureCollection",
    features: payload.map((annotation: any) => ({
      type: "Feature",
      id: annotation.id,
      geometry: annotation.geometry,
      properties: {
        annotation_id: annotation.id,
        annotation_type: annotation.type.replace(/_/g, " "),
        description: annotation.description,
        status: annotation.status,
        source: annotation.source,
        created_at: annotation.created_at
      }
    }))
  };
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
    body: JSON.stringify({
      type: annotation.annotationType.replace(/ /g, "_"),
      description: annotation.description,
      geometry: {
        type: "Point",
        coordinates: [annotation.longitude, annotation.latitude]
      },
      source: "frontend"
    })
  });

  const payload = await response.json();

  if (payload.type === "Feature" && payload.properties) {
    return payload;
  }

  return {
    type: "Feature",
    id: payload.id,
    geometry: payload.geometry,
    properties: {
      annotation_id: payload.id,
      annotation_type: payload.type.replace(/_/g, " "),
      description: payload.description,
      status: payload.status,
      source: payload.source,
      created_at: payload.created_at
    }
  };
}
