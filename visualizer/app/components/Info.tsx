import React from 'react';

interface InfoProps {
  connectionStatus: string;
  isConnected: boolean;
  points: any[];
  lastUpdate: Date | null;
  connect: () => void;
  disconnect: () => void;
  exportData: () => void;
  importData: (file: File) => void;
  clearScan: () => void;
}

export const Info = ({
  connectionStatus,
  isConnected,
  points,
  lastUpdate,
  connect,
  disconnect,
  exportData,
  importData,
  clearScan,
}: InfoProps) => {
  return (
    <div
      style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        zIndex: 100,
        backgroundColor: 'rgba(0,0,0,0.7)',
        color: 'white',
        padding: '10px',
        borderRadius: '5px',
        maxWidth: '300px',
        fontSize: '14px',
      }}
    >
      <h3 style={{ margin: '0 0 10px 0' }}>LiDAR Point Cloud Visualizer</h3>

      <p>
        <strong>Status:</strong> {connectionStatus}
      </p>
      <p>
        <strong>Connected:</strong> {isConnected ? '✅ Yes' : '❌ No'}
      </p>
      <p>
        <strong>Points:</strong> {points.length}
      </p>
      <p>
        <strong>Last update:</strong>{' '}
        {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : '—'}
      </p>

      <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
        <button
          onClick={connect}
          style={{
            padding: '6px 12px',
            borderRadius: '4px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: '#28a745',
            color: 'white',
          }}
        >
          Connect
        </button>
        <button
          onClick={disconnect}
          style={{
            padding: '6px 12px',
            borderRadius: '4px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: '#dc3545',
            color: 'white',
          }}
        >
          Disconnect
        </button>
      </div>
      <div style={{ marginTop: '10px' }}>
        <button
          onClick={clearScan}
          style={{
            padding: '6px 12px',
            borderRadius: '4px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: '#ffc107',
            color: 'white',
          }}
        >
          Limpiar escaneo
        </button>
      </div>
      <div style={{ marginTop: '10px', display: 'flex', gap: '8px' }}>
        <button
          onClick={exportData}
          style={{
            padding: '6px 12px',
            borderRadius: '4px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: '#007bff',
            color: 'white',
          }}
        >
          Exportar JSON
        </button>
      </div>
      <div style={{ marginTop: '10px', display: 'flex', gap: '8px' }}>
        <input
          style={{
            marginTop: '10px',
          }}
          type='file'
          accept='application/json'
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              importData(e.target.files[0]);
            }
          }}
        />
      </div>
    </div>
  );
};
