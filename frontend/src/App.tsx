import { useCallback, useEffect, useState } from "react";
import { createAnnotation, getAnnotations } from "./api/annotations";
import {
  getBikeLanes,
  getHydrants,
  getRoads,
  getSidewalkRamps
} from "./api/layers";
import { analyzeCorridor } from "./api/corridors";
import { generateCorridorReport } from "./api/reports";
import { AnnotationTool } from "./components/AnnotationTool";
import { CorridorSelector } from "./components/CorridorSelector";
import { Header } from "./components/Header";
import { LayerPanel } from "./components/LayerPanel";
import { Layout } from "./components/Layout";
import { MapView } from "./components/MapView";
import { ReportPanel } from "./components/ReportPanel";
import { Sidebar } from "./components/Sidebar";
import type {
  AnnotationDraft,
  AnnotationFeatureCollection
} from "./types/annotations";
import type { CorridorSummary } from "./types/corridors";
import type { RoadFeatureCollection } from "./types/layers";
import {
  DEFAULT_LAYER_VISIBILITY,
  type BikeLaneFeatureCollection,
  type CurbRampFeatureCollection,
  type HydrantFeatureCollection,
  type LayerId,
  type LayerVisibility
} from "./types/layers";
import type { CorridorReportResult } from "./types/reports";
import type { SelectedFeatureDetails } from "./utils/mapHelpers";

const EMPTY_ROADS: RoadFeatureCollection = { type: "FeatureCollection", features: [] };
const EMPTY_CURB_RAMPS: CurbRampFeatureCollection = { type: "FeatureCollection", features: [] };
const EMPTY_HYDRANTS: HydrantFeatureCollection = { type: "FeatureCollection", features: [] };
const EMPTY_ANNOTATIONS: AnnotationFeatureCollection = { type: "FeatureCollection", features: [] };
const EMPTY_BIKE_LANES: BikeLaneFeatureCollection = {
  type: "FeatureCollection",
  features: []
};

export default function App() {
  const [roads, setRoads] = useState<RoadFeatureCollection>(EMPTY_ROADS);
  const [sidewalkRamps, setSidewalkRamps] =
    useState<CurbRampFeatureCollection>(EMPTY_CURB_RAMPS);
  const [hydrants, setHydrants] = useState<HydrantFeatureCollection>(EMPTY_HYDRANTS);
  const [bikeLanes, setBikeLanes] =
    useState<BikeLaneFeatureCollection>(EMPTY_BIKE_LANES);
  const [annotations, setAnnotations] =
    useState<AnnotationFeatureCollection>(EMPTY_ANNOTATIONS);
  const [visibility, setVisibility] = useState<LayerVisibility>(DEFAULT_LAYER_VISIBILITY);
  const [selectedFeature, setSelectedFeature] = useState<SelectedFeatureDetails | null>(null);
  const [selectedRoadId, setSelectedRoadId] = useState<string | null>(null);
  const [corridorSummary, setCorridorSummary] = useState<CorridorSummary | null>(null);
  const [reportResult, setReportResult] = useState<CorridorReportResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [corridorLoading, setCorridorLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [activityMessage, setActivityMessage] = useState("Loading Eugene GIS layers...");

  useEffect(() => {
    async function loadData() {
      try {
        const [
          nextRoads,
          nextSidewalkRamps,
          nextHydrants,
          nextAnnotations,
          nextBikeLanes
        ] = await Promise.all([
          getRoads(),
          getSidewalkRamps(),
          getHydrants(),
          getAnnotations(),
          getBikeLanes()
        ]);

        setRoads(nextRoads);
        setSidewalkRamps(nextSidewalkRamps);
        setHydrants(nextHydrants);
        setAnnotations(nextAnnotations);
        setBikeLanes(nextBikeLanes);
        setActivityMessage("Eugene infrastructure layers loaded. Ready for corridor review.");
      } catch {
        setActivityMessage("Some Eugene layers are unavailable. Local fallbacks remain active.");
      } finally {
        setLoading(false);
      }
    }

    void loadData();
  }, []);

  const handleRoadSelection = useCallback(async (roadId: string) => {
    setSelectedRoadId(roadId || null);
    setReportResult(null);

    if (!roadId) {
      setCorridorSummary(null);
      return;
    }

    setCorridorLoading(true);
    setActivityMessage("Running corridor analysis...");

    try {
      const summary = await analyzeCorridor(roadId);
      setCorridorSummary(summary);
      setActivityMessage(`Loaded corridor summary for ${summary.name}.`);
    } catch {
      setCorridorSummary(null);
      setActivityMessage("Corridor analysis failed. Verify the selected road and backend.");
    } finally {
      setCorridorLoading(false);
    }
  }, []);

  const handleMapRoadSelection = useCallback(
    (roadId: string) => {
      void handleRoadSelection(roadId);
    },
    [handleRoadSelection]
  );

  function toggleLayer(layerId: LayerId) {
    setVisibility((current) => ({
      ...current,
      [layerId]: !current[layerId]
    }));
  }

  async function handleCreateAnnotation(annotation: AnnotationDraft) {
    const nextFeature = await createAnnotation(annotation);
    setAnnotations((current) => ({
      ...current,
      features: [...current.features, nextFeature]
    }));
    setSelectedFeature({
      id: nextFeature.properties.annotation_id,
      layerId: "annotations",
      title: nextFeature.properties.annotation_type,
      subtitle: "Planner annotation",
      source: nextFeature.properties.source,
      status: nextFeature.properties.status,
      notes: nextFeature.properties.description,
      coordinates: nextFeature.geometry.coordinates
    });
    setActivityMessage("New annotation added to the map.");
  }

  async function handleGenerateReport() {
    if (!corridorSummary) {
      return;
    }

    setReportLoading(true);
    setActivityMessage(`Generating a corridor report for ${corridorSummary.name}...`);

    try {
      const result = await generateCorridorReport(
        corridorSummary.roadId,
        corridorSummary.name
      );
      setReportResult(result);
      setActivityMessage(result.summary);
    } catch {
      setReportResult(null);
      setActivityMessage("Report generation failed. Verify the backend and try again.");
    } finally {
      setReportLoading(false);
    }
  }

  return (
    <div className="page-shell">
      <Header />
      <div className="activity-banner">
        <span className={`status-dot ${loading ? "is-loading" : ""}`} />
        {activityMessage}
      </div>
      <Layout
        sidebar={
          <>
            <Sidebar
              title="Map layers"
              description="Toggle cached City of Eugene infrastructure layers and user annotations."
            >
              <LayerPanel
                visibility={visibility}
                layerCounts={{
                  roads: roads.features.length,
                  sidewalkRamps: sidewalkRamps.features.length,
                  hydrants: hydrants.features.length,
                  bikeLanes: bikeLanes.features.length,
                  annotations: annotations.features.length
                }}
                layerStatuses={{
                  roads: roads.metadata?.status ?? "local fallback",
                  sidewalkRamps: sidewalkRamps.metadata?.status ?? "local fallback",
                  hydrants: hydrants.metadata?.status ?? "local fallback",
                  bikeLanes: bikeLanes.metadata?.status ?? "local fallback",
                  annotations: annotations.metadata?.status ?? "persistent"
                }}
                onToggle={toggleLayer}
              />
            </Sidebar>

            <Sidebar
              title="Corridor selector"
              description="Choose a road corridor from the dropdown or click it directly on the map."
            >
              <CorridorSelector
                roads={roads.features}
                selectedRoadId={selectedRoadId}
                loading={corridorLoading}
                onSelect={handleRoadSelection}
              />
            </Sidebar>

            <Sidebar
              title="Annotation tool"
              description="Create a simple missing curb-cut or field issue annotation."
            >
              <AnnotationTool onCreate={handleCreateAnnotation} />
            </Sidebar>
          </>
        }
        map={
          <MapView
            roads={roads}
            sidewalkRamps={sidewalkRamps}
            hydrants={hydrants}
            bikeLanes={bikeLanes}
            annotations={annotations}
            visibility={visibility}
            selectedFeature={selectedFeature}
            selectedRoadId={selectedRoadId}
            onFeatureSelect={setSelectedFeature}
            onRoadSelect={handleMapRoadSelection}
          />
        }
        aside={
          <>
            <Sidebar
              title="Corridor report"
              description="Review a lightweight summary calculated from the current Eugene layers."
            >
              <ReportPanel
                summary={corridorSummary}
                reportResult={reportResult}
                generating={reportLoading}
                onGenerate={handleGenerateReport}
              />
            </Sidebar>

            <Sidebar
              title="Working assumptions"
              description="Sprint 3 uses cached Eugene GIS data with offline-safe fallbacks."
            >
              <ul className="assumption-list">
                <li>The backend serves normalized files from the local Eugene data cache.</li>
                <li>The frontend falls back to small local samples if the API is unavailable.</li>
                <li>User annotations persist to a local JSON file through the backend.</li>
              </ul>
            </Sidebar>
          </>
        }
      />
    </div>
  );
}
