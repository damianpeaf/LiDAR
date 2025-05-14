'use client'

import dynamic from 'next/dynamic'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Stats } from '@react-three/drei'
import { useState, useEffect, useRef } from 'react'
import { clearLidarData } from '../lib/actions'

// Dynamic import for PointCloud component
const PointCloud = dynamic(() => import('./PointCloud'), {
  ssr: false,
})

// Interface for LiDAR data point
interface LidarPoint {
  r: number;
  theta: number;
  phi: number;
  strength: number;
}

export default function ClientPointCloudWrapper() {
  const [showHelp, setShowHelp] = useState(false)
  const [isPolling, setIsPolling] = useState(true)
  const [isClearing, setIsClearing] = useState(false)
  const [lastPoint, setLastPoint] = useState<LidarPoint | null>(null)
  const [pointCloudKey, setPointCloudKey] = useState(Date.now())
  const [pointCount, setPointCount] = useState(0)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Set up polling for new data
  useEffect(() => {
    // Function to fetch the latest data
    const fetchLatestData = async () => {
      try {
        // Add cache-busting parameter to force fresh fetch
        const response = await fetch(`/puntos.json?t=${new Date().getTime()}`)
        const data = await response.json()
        
        // If we have data and it's different from what we had before
        if (Array.isArray(data) && data.length !== pointCount) {
          // If there's a difference, update the entire point cloud
          // This will replace all points with the new data
          if (data.length > 0) {
            // Update the last point for display
            setLastPoint(data[data.length - 1])
          }
          
          // Update the point count
          setPointCount(data.length)
          
          // Force remount of PointCloud component to refresh all points
          setPointCloudKey(Date.now())
          
          console.log(`Polling: Found ${data.length} points, refreshing visualization`)
        }
      } catch (error) {
        console.error('Error polling for data:', error)
      }
    }

    // Start polling
    if (isPolling) {
      // Initial fetch
      fetchLatestData()
      
      // Set up interval for polling
      pollingIntervalRef.current = setInterval(fetchLatestData, 500) // Poll every 500ms for more responsive updates
    }

    // Clean up on unmount or when polling is disabled
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [isPolling, pointCount])

  // Handle clearing LiDAR data
  const handleClearData = async () => {
    setIsClearing(true)
    try {
      const result = await clearLidarData()
      if (result.success) {
        console.log('LiDAR data cleared successfully')
        // Update the key to force PointCloud component to remount
        setPointCloudKey(Date.now())
        // Reset states
        setLastPoint(null)
        setPointCount(0)
      } else {
        console.error('Failed to clear LiDAR data:', result.message)
      }
    } catch (error) {
      console.error('Error clearing LiDAR data:', error)
    } finally {
      setIsClearing(false)
    }
  }

  // Toggle polling
  const togglePolling = () => {
    setIsPolling(!isPolling)
    if (isPolling && pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
  }

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      {/* Information overlay */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        zIndex: 100,
        backgroundColor: 'rgba(0,0,0,0.7)',
        color: 'white',
        padding: '10px',
        borderRadius: '5px',
        maxWidth: '300px',
        fontSize: '14px'
      }}>
        <h3 style={{ margin: '0 0 10px 0' }}>LiDAR Point Cloud Visualizer</h3>
        
        {/* Polling status */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          marginBottom: '10px' 
        }}>
          <div style={{ 
            width: '10px', 
            height: '10px', 
            borderRadius: '50%', 
            backgroundColor: isPolling ? '#4CAF50' : '#F44336',
            marginRight: '5px'
          }}></div>
          <span>{isPolling ? 'Polling Active' : 'Polling Paused'}</span>
        </div>
        
        {/* Point count */}
        <div style={{ marginBottom: '10px' }}>
          <p style={{ margin: '0' }}>Total Points: {pointCount}</p>
        </div>
        
        {/* Last received point */}
        {lastPoint && (
          <div style={{ marginBottom: '10px', fontSize: '12px' }}>
            <p style={{ margin: '0 0 5px 0' }}><strong>Last Point:</strong></p>
            <p style={{ margin: '0' }}>r: {lastPoint.r.toFixed(2)} mm</p>
            <p style={{ margin: '0' }}>θ: {lastPoint.theta.toFixed(2)}°</p>
            <p style={{ margin: '0' }}>φ: {lastPoint.phi.toFixed(2)}°</p>
            <p style={{ margin: '0' }}>strength: {lastPoint.strength}</p>
          </div>
        )}
        
        {/* Controls */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '10px', flexWrap: 'wrap' }}>
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
            onClick={togglePolling}
            style={{
              background: isPolling ? '#F44336' : '#4CAF50',
              border: 'none',
              color: 'white',
              padding: '5px 10px',
              borderRadius: '3px',
              cursor: 'pointer',
            }}
          >
            {isPolling ? 'Pause Polling' : 'Resume Polling'}
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
              opacity: isClearing ? 0.7 : 1
            }}
          >
            {isClearing ? 'Clearing...' : 'Clear Data'}
          </button>
        </div>
        
        {showHelp && (
          <div>
            <p><strong>Navigation:</strong></p>
            <ul style={{ paddingLeft: '20px', margin: '5px 0' }}>
              <li>Left-click + drag: Rotate</li>
              <li>Right-click + drag: Pan</li>
              <li>Scroll: Zoom</li>
            </ul>
            <p><strong>Visualization:</strong></p>
            <ul style={{ paddingLeft: '20px', margin: '5px 0' }}>
              <li>Red sphere: Sensor position (0,0,0)</li>
              <li>Colored points: Point cloud data</li>
              <li>Color gradient: Blue (far) to Red (close)</li>
              <li>Axes: X (red), Y (green), Z (blue)</li>
              <li>Grid: XY plane reference</li>
              <li>Gray circle: Horizontal "floor" plane (φ = 60°)</li>
            </ul>
            
            <p><strong>Coordinate System:</strong></p>
            <ul style={{ paddingLeft: '20px', margin: '5px 0' }}>
              <li>φ = 0°: Looking straight up (vertical)</li>
              <li>φ = 60°: Horizontal plane ("floor")</li>
              <li>θ: Angle around horizontal plane (0-360°)</li>
              <li>r: Distance from sensor</li>
            </ul>
          </div>
        )}
      </div>

      <Canvas 
        camera={{ 
          // Position camera to better show the transformed coordinate system
          position: [150, 150, 100], 
          fov: 60,
          near: 1,
          far: 1000
        }}
      >
        <color attach="background" args={['#111']} />
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
  )
}
