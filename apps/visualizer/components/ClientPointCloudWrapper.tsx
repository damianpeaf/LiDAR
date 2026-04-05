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
    importFromURL,
    clearScan,
  } = useLidar();

  return (
    <div className="w-screen h-screen relative">
      <Info
        connectionStatus={connectionStatus}
        isConnected={isConnected}
        points={points}
        lastUpdate={lastUpdate}
        connect={connect}
        disconnect={disconnect}
        exportData={exportData}
        importData={importData}
        importFromURL={importFromURL}
        clearScan={clearScan}
      />

      <PointCloud points={points} />
    </div>
  );
}
