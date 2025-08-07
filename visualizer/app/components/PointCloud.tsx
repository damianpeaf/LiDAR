import { useEffect, useState, useMemo } from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';
import { Html } from '@react-three/drei';

interface PointData {
  r: number;
  t: number;
  f: number;
  strength?: number;
}

// Get Flask URL from environment or use default
const FLASK_URL = process.env.NEXT_PUBLIC_FLASK_URL || 'http://127.0.0.1:3000';

// Simple spherical to cartesian conversion
function sphericalToCartesian(r: number, theta: number, phi: number) {
  const rad = (deg: number) => deg * (Math.PI / 180);

  const t = rad(theta);
  const p = rad(phi);

  // Standard spherical to cartesian conversion
  const x = r * Math.sin(p) * Math.cos(t);
  const y = r * Math.sin(p) * Math.sin(t);
  const z = r * Math.cos(p);

  return [x, y, z];
}

export default function PointCloud() {
  const [points, setPoints] = useState<PointData[]>([]);
  const [loadingError, setLoadingError] = useState<string>('');

  // Load points from Flask API
  useEffect(() => {
    const fetchPoints = async () => {
      try {
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

        const data: PointData[] = await response.json();

        console.log('PointCloud: Loaded points from API:', data.length);

        // Validate data structure
        const validPoints = data.filter(
          (point) =>
            point &&
            typeof point.r === 'number' &&
            typeof point.t === 'number' &&
            typeof point.f === 'number'
        );

        if (validPoints.length !== data.length) {
          console.warn(
            `PointCloud: Filtered out ${
              data.length - validPoints.length
            } invalid points`
          );
        }

        setPoints(validPoints);
        setLoadingError('');
      } catch (err) {
        console.error('PointCloud: Error loading point cloud data:', err);
        setLoadingError(err instanceof Error ? err.message : 'Unknown error');
        setPoints([]);
      }
    };

    fetchPoints();
  }, []);

  const positions = useMemo(() => {
    const array = new Float32Array(
      points.flatMap((p) => sphericalToCartesian(p.r, p.t, p.f))
    );
    return new THREE.BufferAttribute(array, 3);
  }, [points]);

  // Calculate color based on distance (r value)
  const colors = useMemo(() => {
    if (points.length === 0)
      return new THREE.BufferAttribute(new Float32Array(0), 3);

    const colorArray = new Float32Array(points.length * 3);

    // Find min and max distances for better color mapping
    const distances = points.map((p) => p.r);
    const minDistance = Math.min(...distances);
    const maxDistance = Math.max(...distances);
    const range = maxDistance - minDistance || 1; // Avoid division by zero

    points.forEach((point, i) => {
      // Normalize distance for color mapping
      const normalizedDistance = (point.r - minDistance) / range;

      // Create a color gradient from blue (far) to red (close)
      const color = new THREE.Color();
      color.setHSL(0.7 - normalizedDistance * 0.7, 1, 0.5);

      colorArray[i * 3] = color.r;
      colorArray[i * 3 + 1] = color.g;
      colorArray[i * 3 + 2] = color.b;
    });

    return new THREE.BufferAttribute(colorArray, 3);
  }, [points]);

  // Get the scene to add helpers
  const { scene } = useThree();

  // Add helpers
  useEffect(() => {
    // Add axes helper
    const axesHelper = new THREE.AxesHelper(100);
    scene.add(axesHelper);

    // Add grid helper for the XY plane
    const gridHelper = new THREE.GridHelper(500, 50);
    scene.add(gridHelper);

    // Clean up on unmount
    return () => {
      scene.remove(axesHelper);
      scene.remove(gridHelper);
    };
  }, [scene]);

  return (
    <>
      {/* Origin marker (sensor position) */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[5, 16, 16]} />
        <meshBasicMaterial color='red' />
        <Html distanceFactor={10}>
          <div
            style={{
              backgroundColor: 'rgba(0,0,0,0.7)',
              color: 'white',
              padding: '5px 10px',
              borderRadius: '5px',
              fontSize: '12px',
              whiteSpace: 'nowrap',
            }}
          >
            Sensor (0,0,0)
          </div>
        </Html>
      </mesh>

      {/* Coordinate system reference markers */}
      <mesh position={[0, 0, 0]}>
        <Html position={[0, 0, 100]} distanceFactor={10}>
          <div
            style={{
              backgroundColor: 'rgba(0,0,0,0.7)',
              color: 'white',
              padding: '5px 10px',
              borderRadius: '5px',
              fontSize: '12px',
              whiteSpace: 'nowrap',
            }}
          >
            φ = 0° (Z-axis)
          </div>
        </Html>
      </mesh>

      <mesh>
        <Html position={[100, 0, 0]} distanceFactor={10}>
          <div
            style={{
              backgroundColor: 'rgba(0,0,0,0.7)',
              color: 'white',
              padding: '5px 10px',
              borderRadius: '5px',
              fontSize: '12px',
              whiteSpace: 'nowrap',
            }}
          >
            φ = 90° (XY plane)
          </div>
        </Html>
      </mesh>

      <mesh>
        <Html position={[0, 100, 0]} distanceFactor={10}>
          <div
            style={{
              backgroundColor: 'rgba(0,0,0,0.7)',
              color: 'white',
              padding: '5px 10px',
              borderRadius: '5px',
              fontSize: '12px',
              whiteSpace: 'nowrap',
            }}
          >
            θ = 90° (Y-axis)
          </div>
        </Html>
      </mesh>

      {/* Point cloud */}
      {points.length > 0 && (
        <points>
          <bufferGeometry>
            <primitive attach='attributes-position' object={positions} />
            <primitive attach='attributes-color' object={colors} />
          </bufferGeometry>
          <pointsMaterial
            size={3}
            vertexColors
            sizeAttenuation={true}
            transparent={true}
            opacity={0.8}
          />
        </points>
      )}

      {/* Point count and status display */}
      <Html position={[-150, 150, 0]} distanceFactor={10}>
        <div
          style={{
            backgroundColor: 'rgba(0,0,0,0.7)',
            color: 'white',
            padding: '5px 10px',
            borderRadius: '5px',
            fontSize: '12px',
            whiteSpace: 'nowrap',
          }}
        >
          {loadingError ? (
            <span style={{ color: '#ff6b6b' }}>Error: {loadingError}</span>
          ) : (
            <span>Points: {points.length}</span>
          )}
        </div>
      </Html>

      {/* Distance range info */}
      {points.length > 0 && (
        <Html position={[-150, 130, 0]} distanceFactor={10}>
          <div
            style={{
              backgroundColor: 'rgba(0,0,0,0.7)',
              color: 'white',
              padding: '5px 10px',
              borderRadius: '5px',
              fontSize: '11px',
              whiteSpace: 'nowrap',
            }}
          >
            Range: {Math.min(...points.map((p) => p.r)).toFixed(1)} -{' '}
            {Math.max(...points.map((p) => p.r)).toFixed(1)} mm
          </div>
        </Html>
      )}
    </>
  );
}
