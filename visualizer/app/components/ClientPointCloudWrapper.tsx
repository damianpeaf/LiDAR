'use client';

import dynamic from 'next/dynamic';

import { useLidar } from './useLidar';
import { Info } from './Info';

// Dynamic import for PointCloud component
const PointCloud = dynamic(() => import('./PointCloud'), {
  ssr: false,
});

export default function ClientPointCloudWrapper() {
  const {
    isConnected,
    points,
    connectionStatus,
    lastUpdate,
    connect,
    disconnect,
    exportData,
    importData,
    clearScan,
  } = useLidar();

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <Info
        connectionStatus={connectionStatus}
        isConnected={isConnected}
        points={points}
        lastUpdate={lastUpdate}
        connect={connect}
        disconnect={disconnect}
        exportData={exportData}
        importData={importData}
        clearScan={clearScan}
      />

      <PointCloud points={points} />
    </div>
  );
}
