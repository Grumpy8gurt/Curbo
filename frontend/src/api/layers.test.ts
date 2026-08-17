import { afterEach, describe, expect, it, vi } from "vitest";
import { getRoads } from "./layers";

describe("getRoads", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("bypasses the browser cache so refreshes receive a complete road collection", async () => {
    const roads = {
      type: "FeatureCollection" as const,
      features: []
    };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(roads), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );

    const result = await getRoads();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/layers/roads",
      expect.objectContaining({ cache: "no-store" })
    );
    expect(result).toEqual(roads);
  });
});
