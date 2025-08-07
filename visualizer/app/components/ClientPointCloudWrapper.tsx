'use client';

import dynamic from 'next/dynamic';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stats } from '@react-three/drei';
import { useState, useEffect } from 'react';

// Dynamic import for PointCloud component
const PointCloud = dynamic(() => import('./PointCloud'), {
  ssr: false,
});

// Interface for LiDAR data point from new API
interface LidarPoint {
  r: number;
  t: number;
  f: number;
  strength?: number;
}

// Get Flask URL from environment or use default
const FLASK_URL = 'http://127.0.0.1:3000';

export default function ClientPointCloudWrapper() {
  const [showHelp, setShowHelp] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [lastPoint, setLastPoint] = useState<LidarPoint | null>(null);
  const [pointCloudKey, setPointCloudKey] = useState(Date.now());
  const [pointCount, setPointCount] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState<
    'idle' | 'loading' | 'success' | 'error'
  >('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');

  // Function to fetch data from Flask API
  const fetchData = async () => {
    setIsLoading(true);
    setConnectionStatus('loading');
    setErrorMessage('');

    try {
      // Fetch from Flask API
      const response = await fetch(`${FLASK_URL}/api/lidar-data`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        cache: 'no-cache',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: LidarPoint[] = await response.json();
      setConnectionStatus('success');

      // Debug: log the structure of received data
      if (data.length > 0) {
        console.log('Sample data point:', data[0]);
      }

      // Update point count
      setPointCount(data.length);

      // Update the last point for display - validate the data first
      if (data.length > 0) {
        const lastPointData = data[data.length - 1];
        if (
          lastPointData &&
          typeof lastPointData.r === 'number' &&
          typeof lastPointData.t === 'number' &&
          typeof lastPointData.f === 'number'
        ) {
          setLastPoint(lastPointData);
        } else {
          console.warn('Invalid last point data:', lastPointData);
          setLastPoint(null);
        }
      } else {
        setLastPoint(null);
      }

      // Force remount of PointCloud component to refresh all points
      setPointCloudKey(Date.now());

      console.log(`Loaded ${data.length} points`);
    } catch (error) {
      console.error('Error fetching data:', error);
      setConnectionStatus('error');
      setErrorMessage(
        error instanceof Error ? error.message : 'Unknown error occurred'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchData();
  }, []);

  // Handle clearing LiDAR data
  const handleClearData = async () => {
    setIsClearing(true);
    try {
      const response = await fetch(`${FLASK_URL}/api/clear-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        console.log('LiDAR data cleared successfully:', result);
        // Update the key to force PointCloud component to remount
        setPointCloudKey(Date.now());
        // Reset states
        setLastPoint(null);
        setPointCount(0);
        setConnectionStatus('idle');
      } else {
        console.error('Failed to clear LiDAR data:', response.statusText);
        setErrorMessage(`Failed to clear data: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error clearing LiDAR data:', error);
      setErrorMessage(
        error instanceof Error ? error.message : 'Error clearing data'
      );
    } finally {
      setIsClearing(false);
    }
  };

  // Get status color based on connection status
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'success':
        return '#4CAF50';
      case 'loading':
        return '#FF9800';
      case 'error':
        return '#F44336';
      case 'idle':
        return '#9E9E9E';
      default:
        return '#9E9E9E';
    }
  };

  // Get status text
  const getStatusText = () => {
    switch (connectionStatus) {
      case 'success':
        return 'Data Loaded Successfully';
      case 'loading':
        return 'Loading Data...';
      case 'error':
        return `Error: ${errorMessage}`;
      case 'idle':
        return 'Ready';
      default:
        return 'Unknown Status';
    }
  };

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      {/* Information overlay */}
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

        {/* Connection status */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '10px',
          }}
        >
          <div
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: getStatusColor(),
              marginRight: '5px',
            }}
          ></div>
          <span style={{ fontSize: '12px' }}>{getStatusText()}</span>
        </div>

        {/* API URL */}
        <div style={{ marginBottom: '10px', fontSize: '11px', opacity: 0.8 }}>
          <p style={{ margin: '0' }}>API: {FLASK_URL}</p>
        </div>

        {/* Point count */}
        <div style={{ marginBottom: '10px' }}>
          <p style={{ margin: '0' }}>Total Points: {pointCount}</p>
        </div>

        {/* Last received point */}
        {lastPoint && (
          <div style={{ marginBottom: '10px', fontSize: '12px' }}>
            <p style={{ margin: '0 0 5px 0' }}>
              <strong>Last Point:</strong>
            </p>
            <p style={{ margin: '0' }}>
              r:{' '}
              {typeof lastPoint.r === 'number' ? lastPoint.r.toFixed(2) : 'N/A'}{' '}
              mm
            </p>
            <p style={{ margin: '0' }}>
              θ:{' '}
              {typeof lastPoint.t === 'number' ? lastPoint.t.toFixed(2) : 'N/A'}
              °
            </p>
            <p style={{ margin: '0' }}>
              φ:{' '}
              {typeof lastPoint.f === 'number' ? lastPoint.f.toFixed(2) : 'N/A'}
              °
            </p>
            {lastPoint.strength !== undefined &&
              typeof lastPoint.strength === 'number' && (
                <p style={{ margin: '0' }}>strength: {lastPoint.strength}</p>
              )}
          </div>
        )}

        {/* Controls */}
        <div
          style={{
            display: 'flex',
            gap: '10px',
            marginBottom: '10px',
            flexWrap: 'wrap',
          }}
        >
          <button
            onClick={() => setShowHelp(!showHelp)}
            style={{
              background: '#4a4a4a',
              border: 'none',
              color: 'white',
              padding: '5px 10px',
              borderRadius: '3px',
              cursor: 'pointer',
            }}
          >
            {showHelp ? 'Hide Help' : 'Show Help'}
          </button>

          <button
            onClick={fetchData}
            disabled={isLoading}
            style={{
              background: '#4CAF50',
              border: 'none',
              color: 'white',
              padding: '5px 10px',
              borderRadius: '3px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.7 : 1,
            }}
          >
            {isLoading ? 'Loading...' : 'Refresh Data'}
          </button>

          <button
            onClick={handleClearData}
            disabled={isClearing}
            style={{
              background: '#F44336',
              border: 'none',
              color: 'white',
              padding: '5px 10px',
              borderRadius: '3px',
              cursor: isClearing ? 'not-allowed' : 'pointer',
              opacity: isClearing ? 0.7 : 1,
            }}
          >
            {isClearing ? 'Clearing...' : 'Clear Data'}
          </button>
        </div>

        {showHelp && (
          <div>
            <p>
              <strong>Navigation:</strong>
            </p>
            <ul style={{ paddingLeft: '20px', margin: '5px 0' }}>
              <li>Left-click + drag: Rotate</li>
              <li>Right-click + drag: Pan</li>
              <li>Scroll: Zoom</li>
            </ul>
            <p>
              <strong>Visualization:</strong>
            </p>
            <ul style={{ paddingLeft: '20px', margin: '5px 0' }}>
              <li>Red sphere: Sensor position (0,0,0)</li>
              <li>Colored points: Point cloud data</li>
              <li>Color gradient: Blue (far) to Red (close)</li>
              <li>Axes: X (red), Y (green), Z (blue)</li>
              <li>Grid: XY plane reference</li>
            </ul>

            <p>
              <strong>Coordinate System:</strong>
            </p>
            <ul style={{ paddingLeft: '20px', margin: '5px 0' }}>
              <li>Spherical to Cartesian conversion</li>
              <li>r: Distance from sensor (radius)</li>
              <li>θ: Azimuthal angle (0-360°)</li>
              <li>φ: Polar angle (0-180°)</li>
            </ul>

            <p>
              <strong>Controls:</strong>
            </p>
            <ul style={{ paddingLeft: '20px', margin: '5px 0' }}>
              <li>Refresh Data: Load latest data from API</li>
              <li>Clear Data: Remove all points from server</li>
            </ul>
          </div>
        )}
      </div>

      <Canvas
        camera={{
          // Position camera to better show the coordinate system
          position: [150, 150, 100],
          fov: 60,
          near: 1,
          far: 1000,
        }}
      >
        <color attach='background' args={['#111']} />
        <ambientLight intensity={0.8} />
        <directionalLight position={[0, 10, 5]} intensity={1} />
        <OrbitControls
          enableDamping={true}
          dampingFactor={0.05}
          rotateSpeed={0.5}
          zoomSpeed={0.5}
        />
        <PointCloud key={pointCloudKey} />
        <Stats />
      </Canvas>
    </div>
  );
}
