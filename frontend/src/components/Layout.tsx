import type { ReactNode } from "react";

interface LayoutProps {
  sidebar: ReactNode;
  map: ReactNode;
  aside: ReactNode;
}

export function Layout({ sidebar, map, aside }: LayoutProps) {
  return (
    <div className="app-shell">
      <div className="app-grid">
        <aside className="sidebar-column" aria-label="Map review controls">{sidebar}</aside>
        <main className="map-column" aria-label="Eugene infrastructure map">{map}</main>
        <aside className="aside-column" aria-label="Corridor evidence">{aside}</aside>
      </div>
    </div>
  );
}
