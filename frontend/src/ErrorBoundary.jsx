import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          background: 'var(--bg-main)',
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--card-bg)',
            border: '1px solid var(--error)',
            borderRadius: '12px',
            padding: '40px',
            maxWidth: '500px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
            <h2 style={{ color: 'var(--error)', marginTop: 0 }}>Something went wrong</h2>
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              We encountered an unexpected error. Please try refreshing the page.
            </p>
            <details style={{
              whiteSpace: 'pre-wrap',
              marginTop: '16px',
              fontSize: '12px',
              color: 'var(--text-tertiary)',
              textAlign: 'left',
              background: 'var(--bg-secondary)',
              padding: '12px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)'
            }}>
              <summary style={{ cursor: 'pointer', marginBottom: '8px', fontWeight: '600' }}>Error details</summary>
              {this.state.error?.toString()}
            </details>
            <button
              onClick={() => window.location.reload()}
              style={{
                marginTop: '24px',
                padding: '10px 24px',
                background: 'var(--gradient-1)',
                color: 'var(--bg-main)',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
