export function Header() {
  return (
    <header className="app-header">
      <div>
        <p className="eyebrow">Sidewalk Surveying and Management Dashboard</p>
        <h1>CURBO</h1>
      </div>
      <div className="header-chip">
        <span className="status-dot" aria-hidden="true" />
        <span>
          <strong>Sprint 4</strong>
          Eugene civic review workspace
        </span>
      </div>
    </header>
  );
}
