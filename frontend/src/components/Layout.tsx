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
        <aside className="sidebar-column">{sidebar}</aside>
        <main className="map-column">{map}</main>
        <aside className="aside-column">{aside}</aside>
      </div>
    </div>
  );
}
