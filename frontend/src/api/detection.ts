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
  status: "stored";
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

  return response.json();
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
    body: JSON.stringify({ upload_id: uploadId })
  });

  return response.json();
}

export async function updateDetectionReviewStatus(
  detectionId: string,
  status: DetectionReviewStatus
): Promise<DetectionFeature | undefined> {
  if (USE_MOCK_API) {
    return resolveMock(updateMockDetectionStatus(detectionId, status), 120);
  }

  const response = await fetch(apiUrl(`/api/detections/${detectionId}`), {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ review_status: status })
  });

  return response.json();
}
