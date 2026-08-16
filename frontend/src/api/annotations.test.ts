import { afterEach, describe, expect, it, vi } from "vitest";
import { createAnnotation, updateAnnotationStatus } from "./annotations";

describe("updateAnnotationStatus", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("PATCHes the selected annotation and returns the updated feature", async () => {
    const updated = {
      type: "Feature" as const,
      id: "ann_004",
      geometry: {
        type: "Point" as const,
        coordinates: [-123.08, 44.05] as [number, number]
      },
      properties: {
        annotation_id: "ann_004",
        annotation_type: "curb cut" as const,
        description: "Measured curb cut",
        status: "reviewed" as const,
        source: "CURBO reviewer",
        created_at: "2026-08-02T23:00:00Z",
        version: 2
      }
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(JSON.stringify(updated), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      );

    const result = await updateAnnotationStatus("ann_004", "reviewed", 1);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/annotations/ann_004",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ status: "reviewed", expectedVersion: 1 })
      })
    );
    expect(result.properties.status).toBe("reviewed");
  });

  it("does not claim an annotation was saved when the API is unreachable", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("offline"));

    await expect(
      createAnnotation({
        annotationType: "other",
        description: "Must reach the server",
        geometry: { type: "Point", coordinates: [-123.08, 44.05] }
      })
    ).rejects.toThrow("API is unreachable");
  });

  it("rejects a malformed API response instead of trusting it", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ unexpected: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );

    await expect(updateAnnotationStatus("ann_004", "reviewed", 1)).rejects.toThrow(
      "expected contract"
    );
  });
});
