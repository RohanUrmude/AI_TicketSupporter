import React from 'react';

const LoadingSpinner = ({ message = 'Loading...' }) => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px 20px',
    gap: '16px'
  }}>
    <div style={{
      width: '40px',
      height: '40px',
      border: '4px solid var(--bg-tertiary)',
      borderTop: '4px solid var(--primary)',
      borderRadius: '50%',
      animation: 'spin 0.8s linear infinite'
    }}></div>
    <p style={{
      color: 'var(--text-secondary)',
      fontSize: '14px',
      margin: 0,
      fontWeight: '500'
    }}>
      {message}
    </p>
  </div>
);

export default LoadingSpinner;

