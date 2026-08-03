import { useCallback, useEffect, useRef, useState } from "react";
import {
  createAnnotation,
  getAnnotations,
  updateAnnotationStatus
} from "./api/annotations";
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
  AnnotationDrawMode,
  AnnotationDraft,
  AnnotationFeatureCollection,
  AnnotationGeometry,
  AnnotationStatus
} from "./types/annotations";
import type { CorridorSummary } from "./types/corridors";
import type { Position } from "./types/geojson";
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
import {
  getFeatureCenter,
  type SelectedFeatureDetails
} from "./utils/mapHelpers";

// Stable empty collections used as initial state so MapView never receives
// undefined props and can render without a null guard on each layer.
const EMPTY_ROADS: RoadFeatureCollection = { type: "FeatureCollection", features: [] };
const EMPTY_CURB_RAMPS: CurbRampFeatureCollection = { type: "FeatureCollection", features: [] };
const EMPTY_HYDRANTS: HydrantFeatureCollection = { type: "FeatureCollection", features: [] };
const EMPTY_ANNOTATIONS: AnnotationFeatureCollection = { type: "FeatureCollection", features: [] };
const EMPTY_BIKE_LANES: BikeLaneFeatureCollection = {
  type: "FeatureCollection",
  features: []
};

export default function App() {
  // --- GIS layer state ---
  const [roads, setRoads] = useState<RoadFeatureCollection>(EMPTY_ROADS);
  const [sidewalkRamps, setSidewalkRamps] =
    useState<CurbRampFeatureCollection>(EMPTY_CURB_RAMPS);
  const [hydrants, setHydrants] = useState<HydrantFeatureCollection>(EMPTY_HYDRANTS);
  const [bikeLanes, setBikeLanes] =
    useState<BikeLaneFeatureCollection>(EMPTY_BIKE_LANES);
  const [annotations, setAnnotations] =
    useState<AnnotationFeatureCollection>(EMPTY_ANNOTATIONS);

  // --- UI state ---
  const [visibility, setVisibility] = useState<LayerVisibility>(DEFAULT_LAYER_VISIBILITY);
  const [selectedFeature, setSelectedFeature] = useState<SelectedFeatureDetails | null>(null);
  const [selectedRoadId, setSelectedRoadId] = useState<string | null>(null);
  const [corridorSummary, setCorridorSummary] = useState<CorridorSummary | null>(null);
  const [reportResult, setReportResult] = useState<CorridorReportResult | null>(null);
  const [drawingMode, setDrawingMode] = useState<AnnotationDrawMode | null>(null);
  const [drawingCoordinates, setDrawingCoordinates] = useState<Position[]>([]);
  const [annotationGeometry, setAnnotationGeometry] =
    useState<AnnotationGeometry | null>(null);

  // --- Loading flags (separate so they don't block the map from rendering) ---
  const [loading, setLoading] = useState(true);
  const [corridorLoading, setCorridorLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [activityMessage, setActivityMessage] = useState("Loading Eugene GIS layers...");
  const selectedRoadIdRef = useRef<string | null>(null);
  const corridorRequestIdRef = useRef(0);
  const reportRequestIdRef = useRef(0);

  // Load all five layers in parallel on mount.  Individual layer failures are
  // caught by fetchJsonWithFallback in the API client, so only a total network
  // failure (TypeError) reaches this catch block.
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
        setActivityMessage("Some Eugene layers are unavailable. Available map information is shown.");
      } finally {
        setLoading(false);
      }
    }

    void loadData();
  }, []);

  const refreshCorridor = useCallback(async (
    roadId: string,
    messages: {
      loading: string;
      success: (summary: CorridorSummary) => string;
      failure: string;
    }
  ): Promise<boolean> => {
    const requestId = ++corridorRequestIdRef.current;
    // Reports are immutable snapshots. Invalidate the current link and any
    // in-flight generation whenever the corridor analysis is refreshed.
    reportRequestIdRef.current += 1;
    setReportResult(null);
    setReportLoading(false);
    setCorridorLoading(true);
    setActivityMessage(messages.loading);

    try {
      const summary = await analyzeCorridor(roadId);
      if (requestId !== corridorRequestIdRef.current) {
        return false;
      }
      setCorridorSummary(summary);
      setActivityMessage(messages.success(summary));
      return true;
    } catch {
      if (requestId !== corridorRequestIdRef.current) {
        return false;
      }
      setCorridorSummary(null);
      setActivityMessage(messages.failure);
      return false;
    } finally {
      if (requestId === corridorRequestIdRef.current) {
        setCorridorLoading(false);
      }
    }
  }, []);

  // Wrapped in useCallback so MapView's onRoadSelect prop reference is stable
  // across re-renders and does not retrigger the map interaction effect.
  const handleRoadSelection = useCallback(async (roadId: string) => {
    const nextRoadId = roadId || null;
    selectedRoadIdRef.current = nextRoadId;
    setSelectedRoadId(nextRoadId);

    if (!nextRoadId) {
      corridorRequestIdRef.current += 1;
      reportRequestIdRef.current += 1;
      setCorridorLoading(false);
      setReportLoading(false);
      setCorridorSummary(null);
      setReportResult(null);
      setActivityMessage("Corridor selection cleared.");
      return;
    }

    await refreshCorridor(nextRoadId, {
      loading: "Running corridor analysis...",
      success: (summary) => `Loaded corridor summary for ${summary.name}.`,
      failure: "Corridor analysis is unavailable. Select another road or try again."
    });
  }, [refreshCorridor]);

  // Adapter so MapView can call onRoadSelect with a plain string instead of
  // returning a Promise, keeping the component signature free of async concerns.
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

  const handleStartDrawing = useCallback((mode: AnnotationDrawMode) => {
    setDrawingMode(mode);
    setDrawingCoordinates([]);
    setAnnotationGeometry(null);
    setSelectedFeature(null);
    setActivityMessage(
      mode === "point"
        ? "Click the map to place the reviewer note."
        : "Click two or more map locations to trace the reviewer note."
    );
  }, []);

  const handleDrawClick = useCallback((position: Position) => {
    setDrawingCoordinates((current) => {
      if (drawingMode === "point") {
        setAnnotationGeometry({ type: "Point", coordinates: position });
        setDrawingMode(null);
        setActivityMessage("Point placed. Add a description and save the annotation.");
        return [position];
      }

      if (drawingMode === "line") {
        const next = [...current, position];
        if (next.length >= 2) {
          setAnnotationGeometry({ type: "LineString", coordinates: next });
        }
        return next;
      }

      return current;
    });
  }, [drawingMode]);

  const handleFinishDrawing = useCallback(() => {
    if (drawingCoordinates.length < 2) {
      setActivityMessage("Add at least two map points before finishing the line.");
      return;
    }
    setAnnotationGeometry({
      type: "LineString",
      coordinates: drawingCoordinates
    });
    setDrawingMode(null);
    setActivityMessage("Line completed. Add a description and save the annotation.");
  }, [drawingCoordinates]);

  const handleCancelDrawing = useCallback(() => {
    setDrawingMode(null);
    setDrawingCoordinates([]);
    setAnnotationGeometry(null);
    setActivityMessage("Annotation placement cancelled.");
  }, []);

  const handleUseManualPoint = useCallback((position: Position) => {
    setDrawingMode(null);
    setDrawingCoordinates([position]);
    setAnnotationGeometry({ type: "Point", coordinates: position });
    setActivityMessage("Coordinate point set. Add a description and save the annotation.");
  }, []);

  async function handleCreateAnnotation(annotation: AnnotationDraft) {
    const nextFeature = await createAnnotation(annotation);
    // Append the new feature to the existing collection without a full refetch.
    setAnnotations((current) => ({
      ...current,
      features: [...current.features, nextFeature]
    }));
    // Immediately select the new annotation so it appears in the popup.
    setSelectedFeature({
      id: nextFeature.properties.annotation_id,
      layerId: "annotations",
      title: nextFeature.properties.annotation_type,
      subtitle: "Planner annotation",
      source: nextFeature.properties.source,
      status: nextFeature.properties.status,
      notes: nextFeature.properties.description,
      geometryLabel:
        nextFeature.geometry.type === "LineString"
          ? `Line note (${nextFeature.geometry.coordinates.length} vertices)`
          : "Point note",
      coordinates: getFeatureCenter(nextFeature.geometry)
    });
    setDrawingMode(null);
    setDrawingCoordinates([]);
    setAnnotationGeometry(null);
    const roadId = selectedRoadIdRef.current;
    if (!roadId) {
      setActivityMessage("New annotation saved and added to the map.");
      return;
    }
    await refreshCorridor(roadId, {
      loading: "Annotation saved. Refreshing the selected corridor...",
      success: (summary) =>
        `Annotation saved; ${summary.name} review signals are current.`,
      failure: "Annotation saved, but the selected corridor could not be refreshed."
    });
  }

  async function handleAnnotationStatusChange(
    annotationId: string,
    status: AnnotationStatus
  ) {
    const updated = await updateAnnotationStatus(annotationId, status);
    setAnnotations((current) => ({
      ...current,
      features: current.features.map((feature) =>
        feature.properties.annotation_id === annotationId ? updated : feature
      )
    }));
    setSelectedFeature((current) =>
      current?.layerId === "annotations" && current.id === annotationId
        ? { ...current, status: updated.properties.status }
        : current
    );
    const roadId = selectedRoadIdRef.current;
    if (!roadId) {
      setActivityMessage(`Annotation status saved as ${status}.`);
      return;
    }
    await refreshCorridor(roadId, {
      loading: `Annotation status saved as ${status}. Refreshing the selected corridor...`,
      success: (summary) =>
        `Annotation status saved as ${status}; ${summary.name} review signals are current.`,
      failure: `Annotation status saved as ${status}, but the selected corridor could not be refreshed.`
    });
  }

  async function handleGenerateReport() {
    if (!corridorSummary) {
      return;
    }

    setReportLoading(true);
    setActivityMessage(`Generating a corridor report for ${corridorSummary.name}...`);
    const requestId = ++reportRequestIdRef.current;

    try {
      const result = await generateCorridorReport(
        corridorSummary.roadId,
        corridorSummary.name
      );
      if (requestId === reportRequestIdRef.current) {
        setReportResult(result);
        setActivityMessage(result.summary);
      }
    } catch {
      if (requestId === reportRequestIdRef.current) {
        setReportResult(null);
        setActivityMessage("Report generation is unavailable. Please try again.");
      }
    } finally {
      if (requestId === reportRequestIdRef.current) {
        setReportLoading(false);
      }
    }
  }

  return (
    <div className="page-shell">
      <Header />
      {/* Activity banner doubles as a loading indicator (animated dot) and
          a status log showing the most recent operation outcome. */}
      <div className="activity-banner" role="status" aria-live="polite" aria-atomic="true">
        <span className={`status-dot ${loading ? "is-loading" : ""}`} aria-hidden="true" />
        {activityMessage}
      </div>
      <Layout
        sidebar={
          <>
            <Sidebar
              title="Map layers"
              description="Explore City of Eugene infrastructure and reviewer annotations."
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
              description="Place point or line notes for bike-lane planning review."
            >
              <AnnotationTool
                geometry={annotationGeometry}
                drawingMode={drawingMode}
                drawingPointCount={drawingCoordinates.length}
                onStartDrawing={handleStartDrawing}
                onFinishDrawing={handleFinishDrawing}
                onCancelDrawing={handleCancelDrawing}
                onUseManualPoint={handleUseManualPoint}
                onCreate={handleCreateAnnotation}
              />
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
            drawingMode={drawingMode}
            drawingCoordinates={drawingCoordinates}
            onFeatureSelect={setSelectedFeature}
            onRoadSelect={handleMapRoadSelection}
            onDrawClick={handleDrawClick}
            onAnnotationStatusChange={handleAnnotationStatusChange}
          />
        }
        aside={
          <>
            <Sidebar
              title="Corridor report"
              description="Review infrastructure and annotation evidence for the selected corridor."
            >
              <ReportPanel
                summary={corridorSummary}
                reportResult={reportResult}
                generating={reportLoading}
                onGenerate={handleGenerateReport}
              />
            </Sidebar>

            <Sidebar
              title="Review guidance"
              description="Use CURBO as a screening and documentation tool."
            >
              <ul className="assumption-list">
                <li>Map layers reflect the infrastructure records currently available to CURBO.</li>
                <li>Reviewer annotations remain visible as part of the corridor history.</li>
                <li>Rejected annotations are excluded from active concern counts.</li>
                <li>Review attention is explainable screening, not a safety or project score.</li>
              </ul>
            </Sidebar>
          </>
        }
      />
    </div>
  );
}
