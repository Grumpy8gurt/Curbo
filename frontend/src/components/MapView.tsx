import { useEffect, useRef, useState } from "react";
import maplibregl, {
  type GeoJSONSource,
  type Map,
  type StyleSpecification
} from "maplibre-gl";
import type {
  AnnotationDrawMode,
  AnnotationFeatureCollection,
  AnnotationStatus
} from "../types/annotations";
import type { Feature, Position } from "../types/geojson";
import type {
  BikeLaneFeatureCollection,
  CurbRampFeatureCollection,
  HydrantFeatureCollection,
  LayerId,
  LayerVisibility,
  RoadFeature,
  RoadFeatureCollection
} from "../types/layers";
import {
  getFeatureCenter,
  toSelectedFeatureDetails,
  type SelectedFeatureDetails
} from "../utils/mapHelpers";
import { FeaturePopup } from "./FeaturePopup";

interface MapViewProps {
  roads: RoadFeatureCollection;
  sidewalkRamps: CurbRampFeatureCollection;
  hydrants: HydrantFeatureCollection;
  bikeLanes: BikeLaneFeatureCollection;
  annotations: AnnotationFeatureCollection;
  visibility: LayerVisibility;
  selectedFeature: SelectedFeatureDetails | null;
  selectedRoadId: string | null;
  drawingMode: AnnotationDrawMode | null;
  drawingCoordinates: Position[];
  onFeatureSelect: (feature: SelectedFeatureDetails) => void;
  onRoadSelect: (roadId: string) => void;
  onDrawClick: (position: Position) => void;
  onAnnotationStatusChange: (
    annotationId: string,
    status: AnnotationStatus
  ) => Promise<void>;
}

// Stable string constants for MapLibre source and layer IDs.
// Using `satisfies Record<LayerId, string>` ensures every LayerId has a
// corresponding entry and catches typos at compile time.
const SOURCE_IDS = {
  roads: "roads-source",
  sidewalkRamps: "sidewalk-ramps-source",
  hydrants: "hydrants-source",
  annotations: "annotations-source",
  bikeLanes: "bike-lanes-source"
} satisfies Record<LayerId, string>;

const LAYER_IDS = {
  roads: "roads-layer",
  sidewalkRamps: "sidewalk-ramps-layer",
  hydrants: "hydrants-layer",
  annotations: "annotations-layer",
  bikeLanes: "bike-lanes-layer"
} satisfies Record<LayerId, string>;

// Road labels live in a separate symbol layer so they can be toggled
// alongside the road line layer without duplicating visibility logic.
const ROAD_LABEL_LAYER_ID = "road-labels-layer";
const ANNOTATION_LINE_LAYER_ID = "annotation-lines-layer";
const DRAFT_SOURCE_ID = "annotation-draft-source";
const DRAFT_LINE_LAYER_ID = "annotation-draft-line-layer";
const DRAFT_POINT_LAYER_ID = "annotation-draft-point-layer";

// Minimal self-contained MapLibre style — no external tile server required.
// The green-tinted background provides enough contrast for the Eugene road network.
// Glyphs are loaded from MapLibre's public demo CDN; swap for a self-hosted
// font server in a production deployment.
const LOCAL_MAP_STYLE: StyleSpecification = {
  version: 8,
  name: "CURBO local style",
  glyphs: "/fonts/{fontstack}/{range}.pbf",
  sources: {},
  layers: [
    {
      id: "curbo-background",
      type: "background",
      paint: {
        "background-color": "#dbe7de"
      }
    }
  ]
};

export function MapView({
  roads,
  sidewalkRamps,
  hydrants,
  bikeLanes,
  annotations,
  visibility,
  selectedFeature,
  selectedRoadId,
  drawingMode,
  drawingCoordinates,
  onFeatureSelect,
  onRoadSelect,
  onDrawClick,
  onAnnotationStatusChange
}: MapViewProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  // hasFittedBoundsRef prevents re-fitting the map every time the roads layer
  // is updated; the auto-fit only runs once after the initial data load.
  const hasFittedBoundsRef = useRef(false);
  const drawingModeRef = useRef<AnnotationDrawMode | null>(drawingMode);
  const onDrawClickRef = useRef(onDrawClick);
  const [mapLoaded, setMapLoaded] = useState(false);

  drawingModeRef.current = drawingMode;
  onDrawClickRef.current = onDrawClick;

  // Effect 1: Initialise the MapLibre instance once on mount.
  // Guard against double-init from React StrictMode by checking both refs.
  // The cleanup removes the map on unmount to avoid WebGL context leaks.
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return;
    }

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: LOCAL_MAP_STYLE,
      // Default centre: downtown Eugene, OR
      center: [-123.0868, 44.0521],
      zoom: 13
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.on("error", (event) => {
      const message =
        event.error instanceof Error ? event.error.message : "Unknown MapLibre error";
      console.warn(`MapLibre runtime warning: ${message}`);
    });

    map.on("load", () => {
      addSources(map);
      addLayers(map);
      wireInteractions(
        map,
        onFeatureSelect,
        onRoadSelect,
        () => drawingModeRef.current !== null
      );
      map.on("click", (event) => {
        if (drawingModeRef.current) {
          onDrawClickRef.current([event.lngLat.lng, event.lngLat.lat]);
        }
      });
      setMapLoaded(true);
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      hasFittedBoundsRef.current = false;
      setMapLoaded(false);
    };
  }, [onFeatureSelect, onRoadSelect]);

  // Effect 2: Sync GeoJSON data into sources whenever the prop data changes.
  // mapLoaded is in the dep array so this runs immediately after map init
  // and ensures the first API response is painted without a full re-render.
  useEffect(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded()) {
      return;
    }

    setSourceData(map, SOURCE_IDS.roads, roads);
    setSourceData(map, SOURCE_IDS.sidewalkRamps, sidewalkRamps);
    setSourceData(map, SOURCE_IDS.hydrants, hydrants);
    setSourceData(map, SOURCE_IDS.annotations, annotations);
    setSourceData(map, SOURCE_IDS.bikeLanes, bikeLanes);

    if (!hasFittedBoundsRef.current && roads.features.length > 0) {
      fitMapToRoads(map, roads);
      hasFittedBoundsRef.current = true;
    }
  }, [mapLoaded, roads, sidewalkRamps, hydrants, bikeLanes, annotations]);

  // Effect 3: Sync layer visibility independently of data updates.
  useEffect(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded()) {
      return;
    }

    syncVisibility(map, visibility);
  }, [visibility]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded()) {
      return;
    }
    setSourceData(map, DRAFT_SOURCE_ID, buildDraftCollection(drawingCoordinates));
    map.getCanvas().style.cursor = drawingMode ? "crosshair" : "";
  }, [mapLoaded, drawingMode, drawingCoordinates]);

  // Effect 4: Fly to the selected road when it changes from the corridor
  // selector or from a direct map click.
  useEffect(() => {
    if (!selectedRoadId || !mapRef.current?.isStyleLoaded()) {
      return;
    }

    const selectedRoad = roads.features.find(
      (feature) => feature.properties.road_id === selectedRoadId
    );

    if (!selectedRoad) {
      return;
    }

    mapRef.current.flyTo({
      center: getFeatureCenter(selectedRoad.geometry),
      zoom: 14.5,
      essential: true
    });
  }, [selectedRoadId, roads]);

  return (
    <div className="map-panel">
      <div ref={mapContainerRef} className="map-canvas" />
      {visibility.annotations ? (
        <div className="annotation-legend" aria-label="Reviewer annotation legend">
          <strong>Reviewer notes</strong>
          <span><i className="legend-swatch is-access" /> Curb access</span>
          <span><i className="legend-swatch is-hydrant" /> Hydrant</span>
          <span><i className="legend-swatch is-bike" /> Bike route</span>
          <span><i className="legend-swatch is-conflict" /> Conflict</span>
        </div>
      ) : null}
      <FeaturePopup
        feature={selectedFeature}
        onAnnotationStatusChange={onAnnotationStatusChange}
      />
    </div>
  );
}

function addSources(map: Map) {
  // All sources start empty; data is pushed via setSourceData after the
  // first API response resolves so the map renders immediately on load.
  map.addSource(SOURCE_IDS.roads, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.sidewalkRamps, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.hydrants, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.annotations, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.bikeLanes, { type: "geojson", data: emptyCollection() });
  map.addSource(DRAFT_SOURCE_ID, { type: "geojson", data: emptyCollection() });
}

function addLayers(map: Map) {
  // Layer z-order is insertion order: roads → bike lanes → point features.
  // This keeps lines underneath interactive circles.
  map.addLayer({
    id: LAYER_IDS.roads,
    type: "line",
    source: SOURCE_IDS.roads,
    paint: {
      "line-color": "#2c3f59",
      "line-width": 4
    }
  });

  map.addLayer({
    id: ROAD_LABEL_LAYER_ID,
    type: "symbol",
    source: SOURCE_IDS.roads,
    filter: ["!=", ["get", "name"], "Unnamed road"],
    minzoom: 9,
    layout: {
      "symbol-placement": "line",
      "symbol-spacing": 280,
      "text-field": ["get", "name"],
      "text-font": ["Open Sans Semibold"],
      "text-size": ["interpolate", ["linear"], ["zoom"], 10, 9, 16, 14],
      "text-letter-spacing": 0.03,
      "text-max-angle": 35,
      "text-padding": 4,
      "text-keep-upright": true
    },
    paint: {
      "text-color": "#172638",
      "text-halo-color": "#f5f2e8",
      "text-halo-width": 1.5,
      "text-halo-blur": 0.5
    }
  });

  map.addLayer({
    id: LAYER_IDS.bikeLanes,
    type: "line",
    source: SOURCE_IDS.bikeLanes,
    paint: {
      "line-color": "#2274a5",
      "line-width": 3,
      "line-opacity": 0.85
    }
  });

  map.addLayer({
    id: LAYER_IDS.sidewalkRamps,
    type: "circle",
    source: SOURCE_IDS.sidewalkRamps,
    paint: {
      "circle-radius": 6,
      "circle-color": "#2fbf9b",
      "circle-stroke-color": "#f3efe4",
      "circle-stroke-width": 2
    }
  });

  map.addLayer({
    id: LAYER_IDS.hydrants,
    type: "circle",
    source: SOURCE_IDS.hydrants,
    paint: {
      "circle-radius": 5,
      "circle-color": "#d95d39",
      "circle-stroke-color": "#f3efe4",
      "circle-stroke-width": 1.5
    }
  });

  map.addLayer({
    id: ANNOTATION_LINE_LAYER_ID,
    type: "line",
    source: SOURCE_IDS.annotations,
    filter: ["==", ["geometry-type"], "LineString"],
    paint: {
      "line-color": annotationColorExpression(),
      "line-width": 6,
      "line-opacity": 0.9,
      "line-dasharray": [2, 1]
    }
  });

  map.addLayer({
    id: LAYER_IDS.annotations,
    type: "circle",
    source: SOURCE_IDS.annotations,
    filter: ["==", ["geometry-type"], "Point"],
    paint: {
      "circle-radius": 7,
      "circle-color": annotationColorExpression(),
      "circle-stroke-color": "#17324d",
      "circle-stroke-width": 2
    }
  });

  map.addLayer({
    id: DRAFT_LINE_LAYER_ID,
    type: "line",
    source: DRAFT_SOURCE_ID,
    filter: ["==", ["geometry-type"], "LineString"],
    paint: {
      "line-color": "#17324d",
      "line-width": 5,
      "line-dasharray": [1, 1]
    }
  });

  map.addLayer({
    id: DRAFT_POINT_LAYER_ID,
    type: "circle",
    source: DRAFT_SOURCE_ID,
    filter: ["==", ["geometry-type"], "Point"],
    paint: {
      "circle-radius": 6,
      "circle-color": "#ffffff",
      "circle-stroke-color": "#17324d",
      "circle-stroke-width": 3
    }
  });
}

function wireInteractions(
  map: Map,
  onFeatureSelect: (feature: SelectedFeatureDetails) => void,
  onRoadSelect: (roadId: string) => void,
  isDrawing: () => boolean
) {
  const interactiveLayerEntries: Array<[LayerId, string]> = [
    ["roads", LAYER_IDS.roads],
    ["sidewalkRamps", LAYER_IDS.sidewalkRamps],
    ["hydrants", LAYER_IDS.hydrants],
    ["bikeLanes", LAYER_IDS.bikeLanes],
    ["annotations", LAYER_IDS.annotations],
    ["annotations", ANNOTATION_LINE_LAYER_ID]
  ];

  interactiveLayerEntries.forEach(([layerId, mapLayerId]) => {
    // Pointer cursor on hover signals that the feature is clickable.
    map.on("mouseenter", mapLayerId, () => {
      map.getCanvas().style.cursor = isDrawing() ? "crosshair" : "pointer";
    });

    map.on("mouseleave", mapLayerId, () => {
      map.getCanvas().style.cursor = isDrawing() ? "crosshair" : "";
    });

    map.on("click", mapLayerId, (event) => {
      if (isDrawing()) {
        return;
      }
      const clicked = event.features?.[0];
      if (!clicked) {
        return;
      }

      // toJSON() produces a plain GeoJSON object without MapLibre internal fields.
      const feature = clicked.toJSON() as Feature;
      const details = toSelectedFeatureDetails(layerId, feature);
      onFeatureSelect(details);

      // Road clicks additionally trigger corridor analysis in App.tsx.
      if (layerId === "roads") {
        onRoadSelect((feature as unknown as RoadFeature).properties.road_id);
      }
    });
  });
}

function setSourceData(map: Map, sourceId: string, data: object) {
  // Optional chaining handles the race where setData is called before the
  // map style has fully loaded and sources are not yet registered.
  const source = map.getSource(sourceId) as GeoJSONSource | undefined;
  source?.setData(data);
}

function syncVisibility(map: Map, visibility: LayerVisibility) {
  // Road labels share the roads toggle so toggling the layer also hides labels.
  map.setLayoutProperty(
    LAYER_IDS.roads,
    "visibility",
    visibility.roads ? "visible" : "none"
  );
  map.setLayoutProperty(
    ROAD_LABEL_LAYER_ID,
    "visibility",
    visibility.roads ? "visible" : "none"
  );
  map.setLayoutProperty(
    LAYER_IDS.sidewalkRamps,
    "visibility",
    visibility.sidewalkRamps ? "visible" : "none"
  );
  map.setLayoutProperty(
    LAYER_IDS.hydrants,
    "visibility",
    visibility.hydrants ? "visible" : "none"
  );
  map.setLayoutProperty(
    LAYER_IDS.bikeLanes,
    "visibility",
    visibility.bikeLanes ? "visible" : "none"
  );
  map.setLayoutProperty(
    LAYER_IDS.annotations,
    "visibility",
    visibility.annotations ? "visible" : "none"
  );
  map.setLayoutProperty(
    ANNOTATION_LINE_LAYER_ID,
    "visibility",
    visibility.annotations ? "visible" : "none"
  );
}

function annotationColorExpression() {
  return [
    "match",
    ["get", "annotation_type"],
    "curb cut",
    "#2fbf9b",
    "missing curb cut",
    "#f0b429",
    "fire hydrant",
    "#d95d39",
    "bike lane gap",
    "#8b5cf6",
    "proposed bike lane",
    "#2274a5",
    "parking/loading conflict",
    "#d97706",
    "intersection safety",
    "#dc2626",
    "drainage/utility conflict",
    "#64748b",
    "obstruction",
    "#b45309",
    "bad data",
    "#6b7280",
    "#f0b429"
  ] as maplibregl.ExpressionSpecification;
}

function buildDraftCollection(coordinates: Position[]) {
  const pointFeatures = coordinates.map((coordinate, index) => ({
    type: "Feature" as const,
    id: `draft-point-${index}`,
    properties: {},
    geometry: {
      type: "Point" as const,
      coordinates: coordinate
    }
  }));

  if (coordinates.length < 2) {
    return { type: "FeatureCollection" as const, features: pointFeatures };
  }

  return {
    type: "FeatureCollection" as const,
    features: [
      {
        type: "Feature" as const,
        id: "draft-line",
        properties: {},
        geometry: {
          type: "LineString" as const,
          coordinates
        }
      },
      ...pointFeatures
    ]
  };
}

function fitMapToRoads(map: Map, roads: RoadFeatureCollection) {
  const bounds = new maplibregl.LngLatBounds();
  let hasCoordinates = false;

  roads.features.forEach((feature) => {
    // Flatten MultiLineString coordinate arrays before extending bounds.
    const coordinates =
      feature.geometry.type === "MultiLineString"
        ? feature.geometry.coordinates.flat()
        : feature.geometry.coordinates;
    coordinates.forEach((coordinate) => {
      bounds.extend(coordinate);
      hasCoordinates = true;
    });
  });

  if (!hasCoordinates) {
    return;
  }

  map.fitBounds(bounds, {
    padding: 48,
    // duration: 0 skips the fly animation on initial load for a snappier experience.
    duration: 0,
    maxZoom: 15
  });
}

function emptyCollection() {
  return {
    type: "FeatureCollection",
    features: []
  };
}
