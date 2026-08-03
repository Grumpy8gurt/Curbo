import { afterEach, describe, expect, it, vi } from "vitest";
import { updateAnnotationStatus } from "./annotations";

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
        created_at: "2026-08-02T23:00:00Z"
      }
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify(updated), { status: 200 }));

    const result = await updateAnnotationStatus("ann_004", "reviewed");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/annotations/ann_004",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ status: "reviewed" })
      })
    );
    expect(result.properties.status).toBe("reviewed");
  });
});
