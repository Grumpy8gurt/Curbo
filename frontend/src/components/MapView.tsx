import { useEffect, useRef } from "react";
import maplibregl, {
  type GeoJSONSource,
  type Map,
  type StyleSpecification
} from "maplibre-gl";
import type { AnnotationFeatureCollection } from "../types/annotations";
import type { DetectionFeatureCollection } from "../types/detections";
import type { Feature } from "../types/geojson";
import type {
  CurbRampFeatureCollection,
  HydrantFeatureCollection,
  LayerId,
  LayerVisibility,
  PlaceholderFeatureCollection,
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
  curbRamps: CurbRampFeatureCollection;
  hydrants: HydrantFeatureCollection;
  annotations: AnnotationFeatureCollection;
  detections: DetectionFeatureCollection;
  placeholders: {
    bikeLanes: PlaceholderFeatureCollection;
    busStops: PlaceholderFeatureCollection;
    parkingZones: PlaceholderFeatureCollection;
    parcels: PlaceholderFeatureCollection;
  };
  visibility: LayerVisibility;
  selectedFeature: SelectedFeatureDetails | null;
  selectedRoadId: string | null;
  onFeatureSelect: (feature: SelectedFeatureDetails) => void;
  onRoadSelect: (roadId: string) => void;
}

const SOURCE_IDS = {
  roads: "roads-source",
  curbRamps: "curb-ramps-source",
  hydrants: "hydrants-source",
  annotations: "annotations-source",
  detections: "detections-source",
  bikeLanes: "bike-lanes-source",
  busStops: "bus-stops-source",
  parkingZones: "parking-zones-source",
  parcels: "parcels-source"
} satisfies Record<LayerId, string>;

const LAYER_IDS = {
  roads: "roads-layer",
  curbRamps: "curb-ramps-layer",
  hydrants: "hydrants-layer",
  annotations: "annotations-layer",
  detections: "detections-layer"
} satisfies Record<"roads" | "curbRamps" | "hydrants" | "annotations" | "detections", string>;

const LOCAL_MAP_STYLE: StyleSpecification = {
  version: 8,
  name: "Curbo local style",
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
  curbRamps,
  hydrants,
  annotations,
  detections,
  placeholders,
  visibility,
  selectedFeature,
  selectedRoadId,
  onFeatureSelect,
  onRoadSelect
}: MapViewProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const hasFittedBoundsRef = useRef(false);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return;
    }

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: LOCAL_MAP_STYLE,
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
      wireInteractions(map, onFeatureSelect, onRoadSelect);
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      hasFittedBoundsRef.current = false;
    };
  }, [onFeatureSelect, onRoadSelect]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded()) {
      return;
    }

    setSourceData(map, SOURCE_IDS.roads, roads);
    setSourceData(map, SOURCE_IDS.curbRamps, curbRamps);
    setSourceData(map, SOURCE_IDS.hydrants, hydrants);
    setSourceData(map, SOURCE_IDS.annotations, annotations);
    setSourceData(map, SOURCE_IDS.detections, detections);
    setSourceData(map, SOURCE_IDS.bikeLanes, placeholders.bikeLanes);
    setSourceData(map, SOURCE_IDS.busStops, placeholders.busStops);
    setSourceData(map, SOURCE_IDS.parkingZones, placeholders.parkingZones);
    setSourceData(map, SOURCE_IDS.parcels, placeholders.parcels);

    if (!hasFittedBoundsRef.current && roads.features.length > 0) {
      fitMapToRoads(map, roads);
      hasFittedBoundsRef.current = true;
    }
  }, [roads, curbRamps, hydrants, annotations, detections, placeholders]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded()) {
      return;
    }

    syncVisibility(map, visibility);
  }, [visibility]);

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
      <FeaturePopup feature={selectedFeature} />
    </div>
  );
}

function addSources(map: Map) {
  map.addSource(SOURCE_IDS.roads, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.curbRamps, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.hydrants, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.annotations, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.detections, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.bikeLanes, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.busStops, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.parkingZones, { type: "geojson", data: emptyCollection() });
  map.addSource(SOURCE_IDS.parcels, { type: "geojson", data: emptyCollection() });
}

function addLayers(map: Map) {
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
    id: LAYER_IDS.curbRamps,
    type: "circle",
    source: SOURCE_IDS.curbRamps,
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
    id: LAYER_IDS.annotations,
    type: "circle",
    source: SOURCE_IDS.annotations,
    paint: {
      "circle-radius": 7,
      "circle-color": "#f0b429",
      "circle-stroke-color": "#17324d",
      "circle-stroke-width": 2
    }
  });

  map.addLayer({
    id: LAYER_IDS.detections,
    type: "circle",
    source: SOURCE_IDS.detections,
    paint: {
      "circle-radius": 8,
      "circle-color": "#8f5aff",
      "circle-opacity": 0.85,
      "circle-stroke-color": "#ffffff",
      "circle-stroke-width": 2
    }
  });
}

function wireInteractions(
  map: Map,
  onFeatureSelect: (feature: SelectedFeatureDetails) => void,
  onRoadSelect: (roadId: string) => void
) {
  const interactiveLayerEntries: Array<[LayerId, string]> = [
    ["roads", LAYER_IDS.roads],
    ["curbRamps", LAYER_IDS.curbRamps],
    ["hydrants", LAYER_IDS.hydrants],
    ["annotations", LAYER_IDS.annotations],
    ["detections", LAYER_IDS.detections]
  ];

  interactiveLayerEntries.forEach(([layerId, mapLayerId]) => {
    map.on("mouseenter", mapLayerId, () => {
      map.getCanvas().style.cursor = "pointer";
    });

    map.on("mouseleave", mapLayerId, () => {
      map.getCanvas().style.cursor = "";
    });

    map.on("click", mapLayerId, (event) => {
      const clicked = event.features?.[0];
      if (!clicked) {
        return;
      }

      const feature = clicked.toJSON() as Feature;
      const details = toSelectedFeatureDetails(layerId, feature);
      onFeatureSelect(details);

      if (layerId === "roads") {
        onRoadSelect((feature as unknown as RoadFeature).properties.road_id);
      }
    });
  });
}

function setSourceData(map: Map, sourceId: string, data: object) {
  const source = map.getSource(sourceId) as GeoJSONSource | undefined;
  source?.setData(data);
}

function syncVisibility(map: Map, visibility: LayerVisibility) {
  map.setLayoutProperty(
    LAYER_IDS.roads,
    "visibility",
    visibility.roads ? "visible" : "none"
  );
  map.setLayoutProperty(
    LAYER_IDS.curbRamps,
    "visibility",
    visibility.curbRamps ? "visible" : "none"
  );
  map.setLayoutProperty(
    LAYER_IDS.hydrants,
    "visibility",
    visibility.hydrants ? "visible" : "none"
  );
  map.setLayoutProperty(
    LAYER_IDS.annotations,
    "visibility",
    visibility.annotations ? "visible" : "none"
  );
  map.setLayoutProperty(
    LAYER_IDS.detections,
    "visibility",
    visibility.detections ? "visible" : "none"
  );
}

function fitMapToRoads(map: Map, roads: RoadFeatureCollection) {
  const bounds = new maplibregl.LngLatBounds();
  let hasCoordinates = false;

  roads.features.forEach((feature) => {
    feature.geometry.coordinates.forEach((coordinate) => {
      bounds.extend(coordinate);
      hasCoordinates = true;
    });
  });

  if (!hasCoordinates) {
    return;
  }

  map.fitBounds(bounds, {
    padding: 48,
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
