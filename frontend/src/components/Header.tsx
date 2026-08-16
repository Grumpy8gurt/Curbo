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
          <strong>Eugene, Oregon</strong>
          Civic mobility review
        </span>
      </div>
    </header>
  );
}
