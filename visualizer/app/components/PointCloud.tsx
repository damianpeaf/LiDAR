import { useEffect, useState, useMemo } from 'react'
import * as THREE from 'three'
import { useThree } from '@react-three/fiber'
import { Html } from '@react-three/drei'

interface PointData {
  r: number
  theta: number
  phi: number
  strength: number
}

// No props needed anymore

function sphericalToCartesian(r: number, theta: number, phi: number) {
  const rad = (deg: number) => deg * (Math.PI / 180)
  
  // Transform phi to match the user's coordinate system
  // phi = 60° is the horizontal plane (floor)
  // phi = 0° is looking straight up (vertical)
  // We need to map this to standard spherical coordinates where:
  // phi = 90° is the horizontal plane
  // phi = 0° is vertical up
  
  // Linear transformation: map [0, 60] to [0, 90]
  // const transformedPhi = phi * (90 / 60)
  
  const t = rad(theta)
  const p = rad(phi)
  
  const x = r * Math.sin(p) * Math.cos(t)
  const y = r * Math.sin(p) * Math.sin(t)
  const z = r * Math.cos(p)
  
  return [x, y, z]
}

export default function PointCloud() {
  const [points, setPoints] = useState<PointData[]>([])

  // Load points from file
  useEffect(() => {
    // Add a cache-busting parameter to force a fresh fetch
    fetch(`/puntos.json?t=${new Date().getTime()}`)
      .then(res => res.json())
      .then(data => {
        console.log('Loaded points from file:', data.length)
        setPoints(data)
      })
      .catch(err => {
        console.error('Error loading point cloud data:', err)
        setPoints([])
      })
  }, [])

  const positions = useMemo(() => {
    const array = new Float32Array(
      points.flatMap(p => sphericalToCartesian(p.r, p.theta, p.phi))
    )
    return new THREE.BufferAttribute(array, 3)
  }, [points])

  // Calculate color based on distance (r value)
  const colors = useMemo(() => {
    if (points.length === 0) return new THREE.BufferAttribute(new Float32Array(0), 3)
    
    const colorArray = new Float32Array(points.length * 3)
    
    points.forEach((point, i) => {
      // Normalize distance for color mapping (assuming max distance is around 500)
      const normalizedDistance = Math.min(point.r / 500, 1)
      
      // Create a color gradient from blue (far) to red (close)
      const color = new THREE.Color()
      color.setHSL(0.7 - normalizedDistance * 0.7, 1, 0.5)
      
      colorArray[i * 3] = color.r
      colorArray[i * 3 + 1] = color.g
      colorArray[i * 3 + 2] = color.b
    })
    
    return new THREE.BufferAttribute(colorArray, 3)
  }, [points])

  // Get the scene to add helpers
  const { scene } = useThree()
  
  // Add helpers
  useEffect(() => {
    // Add axes helper
    const axesHelper = new THREE.AxesHelper(100)
    scene.add(axesHelper)
    
    // Add grid helper for the XZ plane
    const gridHelper = new THREE.GridHelper(500, 50)
    gridHelper.rotation.x = Math.PI / 2
    scene.add(gridHelper)
    
    // Clean up on unmount
    return () => {
      scene.remove(axesHelper)
      scene.remove(gridHelper)
    }
  }, [scene])

  return (
    <>
      {/* Origin marker (sensor position) */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[5, 16, 16]} />
        <meshBasicMaterial color="red" />
        <Html distanceFactor={10}>
          <div style={{ 
            backgroundColor: 'rgba(0,0,0,0.7)', 
            color: 'white', 
            padding: '5px 10px', 
            borderRadius: '5px',
            fontSize: '12px',
            whiteSpace: 'nowrap'
          }}>
            Sensor (0,0,0)
          </div>
        </Html>
      </mesh>
      
      {/* Phi reference markers */}
      <mesh position={[0, 0, 0]}>
        <Html position={[0, 0, 50]} distanceFactor={10}>
          <div style={{ 
            backgroundColor: 'rgba(0,0,0,0.7)', 
            color: 'white', 
            padding: '5px 10px', 
            borderRadius: '5px',
            fontSize: '12px',
            whiteSpace: 'nowrap'
          }}>
            φ = 0° (Vertical)
          </div>
        </Html>
      </mesh>
      
      <mesh>
        <Html position={[100, 0, 0]} distanceFactor={10}>
          <div style={{ 
            backgroundColor: 'rgba(0,0,0,0.7)', 
            color: 'white', 
            padding: '5px 10px', 
            borderRadius: '5px',
            fontSize: '12px',
            whiteSpace: 'nowrap'
          }}>
            φ = 60° (Horizontal "Floor")
          </div>
        </Html>
      </mesh>
      
      {/* Point cloud */}
      <points>
        <bufferGeometry>
          <primitive attach="attributes-position" object={positions} />
          <primitive attach="attributes-color" object={colors} />
        </bufferGeometry>
        <pointsMaterial 
          size={3} 
          vertexColors 
          sizeAttenuation={true} 
          transparent={true}
          opacity={0.8}
        />
      </points>
      
      {/* Point count display */}
      <Html position={[-150, 150, 0]} distanceFactor={10}>
        <div style={{ 
          backgroundColor: 'rgba(0,0,0,0.7)', 
          color: 'white', 
          padding: '5px 10px', 
          borderRadius: '5px',
          fontSize: '12px',
          whiteSpace: 'nowrap'
        }}>
          Points: {points.length}
        </div>
      </Html>
    </>
  )
}
