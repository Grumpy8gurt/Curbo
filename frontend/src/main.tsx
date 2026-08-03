import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/global.css";
// MapLibre ships its own CSS for the map canvas, controls, and popups.
// Importing here ensures it is bundled regardless of which component uses MapLibre.
import "maplibre-gl/dist/maplibre-gl.css";

// React.StrictMode renders every component twice in development to surface
// side effects in lifecycle methods.  This is stripped in the production build.
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
