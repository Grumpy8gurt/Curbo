import type { ReactNode } from "react";

interface SidebarProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function Sidebar({ title, description, children }: SidebarProps) {
  return (
    <section className="panel-card">
      <div className="panel-heading">
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {children}
    </section>
  );
}
