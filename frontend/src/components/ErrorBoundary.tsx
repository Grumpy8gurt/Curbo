import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  failed: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { failed: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("CURBO map rendering failed", error, info.componentStack);
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="map-loading" role="alert">
          The map could not be displayed. Reload the page or try again later.
        </div>
      );
    }
    return this.props.children;
  }
}
