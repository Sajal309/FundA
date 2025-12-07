import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-dark-800 rounded-lg shadow-lg p-6 border border-red-500">
            <div className="text-center mb-6">
              <h1 className="text-2xl font-bold text-red-400 mb-2">
                Something went wrong
              </h1>
              <p className="text-dark-300">
                An error occurred while rendering the application
              </p>
            </div>

            {this.state.error && (
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-red-300 mb-2">
                  Error Details:
                </h2>
                <div className="bg-dark-900 rounded p-4 overflow-auto max-h-48">
                  <pre className="text-sm text-red-200 whitespace-pre-wrap">
                    {this.state.error.toString()}
                  </pre>
                </div>
              </div>
            )}

            {this.state.errorInfo && (
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-red-300 mb-2">
                  Component Stack:
                </h2>
                <div className="bg-dark-900 rounded p-4 overflow-auto max-h-48">
                  <pre className="text-xs text-dark-300 whitespace-pre-wrap">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </div>
              </div>
            )}

            <div className="flex gap-4 justify-center mt-6">
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Reload Page
              </button>
              <button
                onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
                className="px-6 py-2 bg-dark-700 text-dark-200 rounded hover:bg-dark-600 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

