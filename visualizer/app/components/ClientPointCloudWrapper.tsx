'use client'

import dynamic from 'next/dynamic'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Stats } from '@react-three/drei'
import { useState } from 'react'

const PointCloud = dynamic(() => import('./PointCloud'), {
  ssr: false,
})

export default function ClientPointCloudWrapper() {
  const [showHelp, setShowHelp] = useState(false)

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
        <button 
          onClick={() => setShowHelp(!showHelp)}
          style={{
            background: '#4a4a4a',
            border: 'none',
            color: 'white',
            padding: '5px 10px',
            borderRadius: '3px',
            cursor: 'pointer',
            marginBottom: '10px'
          }}
        >
          {showHelp ? 'Hide Help' : 'Show Help'}
        </button>
        
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
        <PointCloud />
        <Stats />
      </Canvas>
    </div>
  )
}
