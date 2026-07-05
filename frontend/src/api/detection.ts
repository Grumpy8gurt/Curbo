import { apiUrl, resolveMock, USE_MOCK_API } from "./client";
import {
  createMockDetectionFromUpload,
  createMockUpload,
  updateMockDetectionStatus
} from "./mockData";
import type {
  DetectionFeature,
  DetectionReviewStatus
} from "../types/detections";

export interface UploadedImageResult {
  uploadId: string;
  filename: string;
  status: "stored" | "uploaded";
}

export async function uploadImage(file: File): Promise<UploadedImageResult> {
  if (USE_MOCK_API) {
    return resolveMock(createMockUpload(file), 220);
  }

  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch(apiUrl("/api/uploads/images"), {
    method: "POST",
    body: formData
  });

  const payload = await response.json();

  return {
    uploadId: payload.uploadId ?? payload.image_id,
    filename: payload.filename,
    status: payload.status
  };
}

export async function runCurbCutDetection(
  uploadId: string
): Promise<DetectionFeature> {
  if (USE_MOCK_API) {
    return resolveMock(createMockDetectionFromUpload(uploadId), 300);
  }

  const response = await fetch(apiUrl("/api/detection/curb-cuts"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ image_id: uploadId })
  });

  const payload = await response.json();

  if (payload.type === "Feature" && payload.properties) {
    return payload;
  }

  const detection = payload.detections[0];

  return {
    type: "Feature",
    id: detection.id,
    geometry: detection.estimated_location,
    properties: {
      detection_id: detection.id,
      label: detection.label,
      confidence: detection.confidence,
      review_status: detection.review_status,
      upload_id: payload.image_id,
      source: "backend",
      bbox: detection.bbox
    }
  };
}

export async function updateDetectionReviewStatus(
  detectionId: string,
  status: DetectionReviewStatus
): Promise<DetectionFeature | undefined> {
  if (USE_MOCK_API) {
    return resolveMock(updateMockDetectionStatus(detectionId, status), 120);
  }

  const response = await fetch(apiUrl(`/api/detection/${detectionId}`), {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ review_status: status })
  });

  const payload = await response.json();

  if (payload.type === "Feature" && payload.properties) {
    return payload;
  }

  return {
    type: "Feature",
    id: payload.id,
    geometry: payload.estimated_location ?? payload.geometry,
    properties: {
      detection_id: payload.id ?? payload.properties?.detection_id,
      label: payload.label,
      confidence: payload.confidence,
      review_status: payload.review_status,
      source: "backend",
      bbox: payload.bbox
    }
  };
}
