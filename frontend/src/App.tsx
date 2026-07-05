import { useEffect, useState } from "react";
import { createAnnotation, getAnnotations } from "./api/annotations";
import {
  runCurbCutDetection,
  updateDetectionReviewStatus,
  uploadImage
} from "./api/detection";
import {
  getCurbRamps,
  getDetections,
  getHydrants,
  getPlaceholderLayer,
  getRoads
} from "./api/layers";
import { analyzeCorridor } from "./api/corridors";
import { generateCorridorReport } from "./api/reports";
import { AnnotationTool } from "./components/AnnotationTool";
import { CorridorSelector } from "./components/CorridorSelector";
import { DetectionReviewPanel } from "./components/DetectionReviewPanel";
import { Header } from "./components/Header";
import { LayerPanel } from "./components/LayerPanel";
import { Layout } from "./components/Layout";
import { MapView } from "./components/MapView";
import { ReportPanel } from "./components/ReportPanel";
import { Sidebar } from "./components/Sidebar";
import { UploadPanel } from "./components/UploadPanel";
import type {
  AnnotationDraft,
  AnnotationFeatureCollection
} from "./types/annotations";
import type { CorridorSummary } from "./types/corridors";
import type {
  DetectionFeatureCollection,
  DetectionReviewStatus
} from "./types/detections";
import type { PlaceholderFeatureCollection, RoadFeatureCollection } from "./types/layers";
import {
  DEFAULT_LAYER_VISIBILITY,
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
const EMPTY_DETECTIONS: DetectionFeatureCollection = { type: "FeatureCollection", features: [] };
const EMPTY_PLACEHOLDERS: PlaceholderFeatureCollection = {
  type: "FeatureCollection",
  features: []
};

export default function App() {
  const [roads, setRoads] = useState<RoadFeatureCollection>(EMPTY_ROADS);
  const [curbRamps, setCurbRamps] = useState<CurbRampFeatureCollection>(EMPTY_CURB_RAMPS);
  const [hydrants, setHydrants] = useState<HydrantFeatureCollection>(EMPTY_HYDRANTS);
  const [annotations, setAnnotations] =
    useState<AnnotationFeatureCollection>(EMPTY_ANNOTATIONS);
  const [detections, setDetections] = useState<DetectionFeatureCollection>(EMPTY_DETECTIONS);
  const [bikeLanes, setBikeLanes] = useState<PlaceholderFeatureCollection>(EMPTY_PLACEHOLDERS);
  const [busStops, setBusStops] = useState<PlaceholderFeatureCollection>(EMPTY_PLACEHOLDERS);
  const [parkingZones, setParkingZones] =
    useState<PlaceholderFeatureCollection>(EMPTY_PLACEHOLDERS);
  const [parcels, setParcels] = useState<PlaceholderFeatureCollection>(EMPTY_PLACEHOLDERS);
  const [visibility, setVisibility] = useState<LayerVisibility>(DEFAULT_LAYER_VISIBILITY);
  const [selectedFeature, setSelectedFeature] = useState<SelectedFeatureDetails | null>(null);
  const [selectedRoadId, setSelectedRoadId] = useState<string | null>(null);
  const [corridorSummary, setCorridorSummary] = useState<CorridorSummary | null>(null);
  const [reportResult, setReportResult] = useState<CorridorReportResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [corridorLoading, setCorridorLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [activityMessage, setActivityMessage] = useState("Loading planning layers...");

  useEffect(() => {
    async function loadData() {
      try {
        const [
          nextRoads,
          nextCurbRamps,
          nextHydrants,
          nextAnnotations,
          nextDetections,
          nextBikeLanes,
          nextBusStops,
          nextParkingZones,
          nextParcels
        ] = await Promise.all([
          getRoads(),
          getCurbRamps(),
          getHydrants(),
          getAnnotations(),
          getDetections(),
          getPlaceholderLayer(),
          getPlaceholderLayer(),
          getPlaceholderLayer(),
          getPlaceholderLayer()
        ]);

        setRoads(nextRoads);
        setCurbRamps(nextCurbRamps);
        setHydrants(nextHydrants);
        setAnnotations(nextAnnotations);
        setDetections(nextDetections);
        setBikeLanes(nextBikeLanes);
        setBusStops(nextBusStops);
        setParkingZones(nextParkingZones);
        setParcels(nextParcels);
        setActivityMessage("Planning layers loaded. Ready for corridor review.");
      } finally {
        setLoading(false);
      }
    }

    void loadData();
  }, []);

  async function handleRoadSelection(roadId: string) {
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
    } finally {
      setCorridorLoading(false);
    }
  }

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

  async function handleUpload(file: File) {
    setActivityMessage(`Uploading ${file.name} to the detection pipeline...`);
    const upload = await uploadImage(file);
    const detection = await runCurbCutDetection(upload.uploadId);
    setDetections((current) => ({
      ...current,
      features: [detection, ...current.features]
    }));
    setSelectedFeature({
      id: detection.properties.detection_id,
      layerId: "detections",
      title: detection.properties.label,
      subtitle: "AI detection",
      source: detection.properties.source,
      status: detection.properties.review_status,
      confidence: detection.properties.confidence,
      coordinates: detection.geometry.coordinates
    });
    setActivityMessage(`Detection created from ${upload.filename}.`);
  }

  async function handleDetectionReview(
    detectionId: string,
    status: DetectionReviewStatus
  ) {
    const updated = await updateDetectionReviewStatus(detectionId, status);
    if (!updated) {
      return;
    }

    setDetections((current) => ({
      ...current,
      features: current.features.map((feature) =>
        feature.properties.detection_id === detectionId ? updated : feature
      )
    }));

    setSelectedFeature((current) =>
      current?.id === detectionId
        ? {
            ...current,
            status
          }
        : current
    );

    setActivityMessage(`Detection ${detectionId} marked ${status}.`);
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
              description="Toggle visibility for the core planning layers. Placeholder layers are listed for future backend work."
            >
              <LayerPanel visibility={visibility} onToggle={toggleLayer} />
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

            <Sidebar
              title="Image upload"
              description="Prototype the future AI pipeline without implementing the model itself."
            >
              <UploadPanel onUpload={handleUpload} />
            </Sidebar>
          </>
        }
        map={
          <MapView
            roads={roads}
            curbRamps={curbRamps}
            hydrants={hydrants}
            annotations={annotations}
            detections={detections}
            placeholders={{ bikeLanes, busStops, parkingZones, parcels }}
            visibility={visibility}
            selectedFeature={selectedFeature}
            selectedRoadId={selectedRoadId}
            onFeatureSelect={setSelectedFeature}
            onRoadSelect={(roadId) => {
              void handleRoadSelection(roadId);
            }}
          />
        }
        aside={
          <>
            <Sidebar
              title="Corridor report"
              description="The backend will eventually own the real spatial analysis and report export."
            >
              <ReportPanel
                summary={corridorSummary}
                reportResult={reportResult}
                generating={reportLoading}
                onGenerate={handleGenerateReport}
              />
            </Sidebar>

            <Sidebar
              title="Detection review"
              description="Review mocked curb-cut candidates and keep their status in sync with the map."
            >
              <DetectionReviewPanel
                detections={detections.features}
                onReview={handleDetectionReview}
              />
            </Sidebar>

            <Sidebar
              title="Working assumptions"
              description="This frontend is intentionally mock-first so the rest of the stack can catch up later."
            >
              <ul className="assumption-list">
                <li>Map layers currently load from sample or local mock GeoJSON.</li>
                <li>Corridor analysis and reporting are simulated in the frontend API layer.</li>
                <li>Uploads create fake detections and do not invoke real ML inference.</li>
                <li>Backend integration can replace the API modules without redesigning the UI.</li>
              </ul>
            </Sidebar>
          </>
        }
      />
    </div>
  );
}
