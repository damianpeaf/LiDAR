import React, { useMemo, useRef, useEffect, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

interface Point {
  intensity: number;
  x: number;
  y: number;
  z: number;
}

interface PointCloudProps {
  points: Point[];
}

// Controles FPS para movimiento tipo videojuego
function FPSControls() {
  const { camera, gl } = useThree();
  const moveSpeed = useRef(2);
  const keys = useRef({
    w: false,
    a: false,
    s: false,
    d: false,
    shift: false,
    space: false,
  });

  const euler = useRef(new THREE.Euler(0, 0, 0, 'YXZ'));
  const vector = useRef(new THREE.Vector3());
  const isLocked = useRef(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const key = event.code.toLowerCase();
      if (key === 'keyw') keys.current.w = true;
      if (key === 'keya') keys.current.a = true;
      if (key === 'keys') keys.current.s = true;
      if (key === 'keyd') keys.current.d = true;
      if (key === 'shiftleft' || key === 'shiftright')
        keys.current.shift = true;
      if (key === 'space') keys.current.space = true;
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      const key = event.code.toLowerCase();
      if (key === 'keyw') keys.current.w = false;
      if (key === 'keya') keys.current.a = false;
      if (key === 'keys') keys.current.s = false;
      if (key === 'keyd') keys.current.d = false;
      if (key === 'shiftleft' || key === 'shiftright')
        keys.current.shift = false;
      if (key === 'space') keys.current.space = false;
    };

    const handleMouseMove = (event: MouseEvent) => {
      if (!isLocked.current) return;

      const movementX = event.movementX || 0;
      const movementY = event.movementY || 0;

      euler.current.setFromQuaternion(camera.quaternion);
      euler.current.y -= movementX * 0.002;
      euler.current.x -= movementY * 0.002;
      euler.current.x = Math.max(
        -Math.PI / 2,
        Math.min(Math.PI / 2, euler.current.x)
      );
      camera.quaternion.setFromEuler(euler.current);
    };

    const handlePointerLockChange = () => {
      isLocked.current = document.pointerLockElement === gl.domElement;
    };

    const handleClick = () => {
      gl.domElement.requestPointerLock();
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('pointerlockchange', handlePointerLockChange);
    gl.domElement.addEventListener('click', handleClick);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener(
        'pointerlockchange',
        handlePointerLockChange
      );
      gl.domElement.removeEventListener('click', handleClick);
    };
  }, [camera, gl]);

  useFrame((_, delta) => {
    if (!isLocked.current) return;

    const speed = keys.current.shift
      ? moveSpeed.current * 3
      : moveSpeed.current;
    const actualSpeed = speed * delta * 60;

    vector.current.set(0, 0, 0);

    if (keys.current.w) vector.current.z -= actualSpeed;
    if (keys.current.s) vector.current.z += actualSpeed;
    if (keys.current.a) vector.current.x -= actualSpeed;
    if (keys.current.d) vector.current.x += actualSpeed;
    if (keys.current.space) vector.current.y += actualSpeed;
    if (keys.current.shift && !keys.current.space)
      vector.current.y -= actualSpeed;

    vector.current.applyQuaternion(camera.quaternion);
    camera.position.add(vector.current);
  });

  return null;
}

// Componente principal de la nube de puntos con capacidades avanzadas
function AdvancedPointCloud({
  points,
  renderMode,
  pointSize,
  opacity,
}: {
  points: Point[];
  renderMode: 'intensity' | 'height' | 'distance' | 'rainbow';
  pointSize: number;
  opacity: number;
}) {
  const pointsRef = useRef<THREE.Points>(null);

  // Calcular posiciones y metadatos de forma optimizada
  const { positions, colors, bounds } = useMemo(() => {
    if (points.length === 0)
      return { positions: null, colors: null, bounds: null };

    // Calcular bounds en una sola pasada - MUY IMPORTANTE para arrays grandes
    let minX = Infinity,
      maxX = -Infinity;
    let minY = Infinity,
      maxY = -Infinity;
    let minZ = Infinity,
      maxZ = -Infinity;
    let minIntensity = Infinity,
      maxIntensity = -Infinity;

    // Una sola iteración para encontrar todos los bounds
    for (let i = 0; i < points.length; i++) {
      const point = points[i];

      if (point.x < minX) minX = point.x;
      if (point.x > maxX) maxX = point.x;
      if (point.y < minY) minY = point.y;
      if (point.y > maxY) maxY = point.y;
      if (point.z < minZ) minZ = point.z;
      if (point.z > maxZ) maxZ = point.z;
      if (point.intensity < minIntensity) minIntensity = point.intensity;
      if (point.intensity > maxIntensity) maxIntensity = point.intensity;
    }

    const bounds = {
      minX,
      maxX,
      minY,
      maxY,
      minZ,
      maxZ,
      minIntensity,
      maxIntensity,
    };

    const center = new THREE.Vector3(
      (bounds.minX + bounds.maxX) / 2,
      (bounds.minY + bounds.maxY) / 2,
      (bounds.minZ + bounds.maxZ) / 2
    );

    // Pre-calcular valores para optimizar el bucle principal
    const rangeX = bounds.maxX - bounds.minX || 1;
    const rangeY = bounds.maxY - bounds.minY || 1;
    const rangeZ = bounds.maxZ - bounds.minZ || 1;
    const rangeIntensity = bounds.maxIntensity - bounds.minIntensity || 1;

    // Calcular distancia máxima una sola vez
    const maxDistance = Math.sqrt(
      (rangeX / 2) ** 2 + (rangeY / 2) ** 2 + (rangeZ / 2) ** 2
    );

    // Crear arrays de buffer
    const posArray = new Float32Array(points.length * 3);
    const colorArray = new Float32Array(points.length * 3);

    // Una sola iteración para posiciones y colores
    for (let i = 0; i < points.length; i++) {
      const point = points[i];
      const idx3 = i * 3;

      // Posiciones centradas
      posArray[idx3] = point.x - center.x;
      posArray[idx3 + 1] = point.y - center.y;
      posArray[idx3 + 2] = point.z - center.z;

      // Calcular color según modo de renderizado
      let r, g, b;

      switch (renderMode) {
        case 'intensity': {
          const intensity =
            (point.intensity - bounds.minIntensity) / rangeIntensity;
          const hue = 0.15 + intensity * 0.5;
          const lightness = 0.5 + intensity * 0.3;
          // Convertir HSL a RGB de forma optimizada
          const color = new THREE.Color().setHSL(hue, 1, lightness);
          r = color.r;
          g = color.g;
          b = color.b;
          break;
        }
        case 'height': {
          const height = (point.z - bounds.minZ) / rangeZ;
          const hue = 0.7 - height * 0.7;
          const color = new THREE.Color().setHSL(hue, 1, 0.5);
          r = color.r;
          g = color.g;
          b = color.b;
          break;
        }
        case 'distance': {
          const distance = Math.sqrt(
            (point.x - center.x) ** 2 +
              (point.y - center.y) ** 2 +
              (point.z - center.z) ** 2
          );
          const normalizedDistance = distance / maxDistance;
          const hue = 0.8 - normalizedDistance * 0.6;
          const color = new THREE.Color().setHSL(hue, 1, 0.6);
          r = color.r;
          g = color.g;
          b = color.b;
          break;
        }
        case 'rainbow': {
          const angle =
            Math.atan2(point.y - center.y, point.x - center.x) + Math.PI;
          const hue = (angle / (2 * Math.PI)) % 1;
          const color = new THREE.Color().setHSL(hue, 1, 0.6);
          r = color.r;
          g = color.g;
          b = color.b;
          break;
        }
        default:
          r = g = b = 1;
      }

      colorArray[idx3] = r;
      colorArray[idx3 + 1] = g;
      colorArray[idx3 + 2] = b;
    }

    return {
      positions: new THREE.BufferAttribute(posArray, 3),
      colors: new THREE.BufferAttribute(colorArray, 3),
      bounds,
    };
  }, [points, renderMode]);

  // Animación optimizada
  useFrame((state) => {
    if (pointsRef.current) {
      const material = pointsRef.current.material as THREE.PointsMaterial;
      // Solo actualizar si el tamaño ha cambiado significativamente
      const newSize = pointSize + Math.sin(state.clock.elapsedTime * 0.5) * 0.2;
      if (Math.abs(material.size - newSize) > 0.01) {
        material.size = newSize;
      }
    }
  });

  if (!positions || !colors) return null;

  return (
    <>
      {/* Nube de puntos principal */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <primitive attach='attributes-position' object={positions} />
          <primitive attach='attributes-color' object={colors} />
        </bufferGeometry>
        <pointsMaterial
          size={pointSize}
          vertexColors
          sizeAttenuation={false}
          transparent
          opacity={opacity}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>

      {/* Puntos adicionales con efecto de profundidad */}
      <points>
        <bufferGeometry>
          <primitive attach='attributes-position' object={positions} />
          <primitive attach='attributes-color' object={colors} />
        </bufferGeometry>
        <pointsMaterial
          size={pointSize * 0.3}
          vertexColors
          sizeAttenuation={true}
          transparent
          opacity={opacity * 0.6}
          depthTest={true}
        />
      </points>
    </>
  );
}

// Grid de referencia opcional
function ReferenceGrid({ size = 100, divisions = 20 }) {
  const gridRef = useRef<THREE.GridHelper>(null);
  const axesRef = useRef<THREE.AxesHelper>(null);

  return (
    <group>
      <primitive
        object={new THREE.GridHelper(size, divisions)}
        position={[0, -size / 4, 0]}
        ref={gridRef}
      />
      <primitive object={new THREE.AxesHelper(size / 4)} ref={axesRef} />
    </group>
  );
}

export default function PointCloudVisualizer({ points }: PointCloudProps) {
  const [showGrid, setShowGrid] = useState(false);
  const [renderMode, setRenderMode] = useState<
    'intensity' | 'height' | 'distance' | 'rainbow'
  >('intensity');
  const [pointSize, setPointSize] = useState(2.5);
  const [opacity, setOpacity] = useState(0.9);

  if (points.length === 0) {
    return (
      <div className='w-full h-screen flex items-center justify-center bg-gray-900 text-white'>
        <div className='text-center'>
          <h2 className='text-2xl font-bold mb-2'>LiDAR Visualizer</h2>
          <p className='text-gray-400'>No hay puntos para mostrar</p>
        </div>
      </div>
    );
  }

  return (
    <div className='w-full h-screen relative bg-black'>
      {/* Controles UI fuera del Canvas */}
      <div className='absolute top-4 right-4 z-10 bg-black/80 backdrop-blur-sm rounded-lg p-4 text-white'>
        <div className='space-y-3'>
          <div>
            <span className='block text-sm font-medium mb-2'>
              Modo de Color
            </span>
            <select
              value={renderMode}
              onChange={(e) => setRenderMode(e.target.value as any)}
              className='w-full bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm'
            >
              <option value='intensity'>Intensidad</option>
              <option value='height'>Altura</option>
              <option value='distance'>Distancia</option>
              <option value='rainbow'>Arcoíris</option>
            </select>
          </div>

          <div>
            <span className='block text-sm font-medium mb-2'>
              Tamaño: {pointSize.toFixed(1)}
            </span>
            <input
              type='range'
              min='0.5'
              max='8'
              step='0.1'
              value={pointSize}
              onChange={(e) => setPointSize(parseFloat(e.target.value))}
              className='w-full'
            />
          </div>

          <div>
            <span className='block text-sm font-medium mb-2'>
              Opacidad: {Math.round(opacity * 100)}%
            </span>
            <input
              type='range'
              min='0.2'
              max='1'
              step='0.05'
              value={opacity}
              onChange={(e) => setOpacity(parseFloat(e.target.value))}
              className='w-full'
            />
          </div>

          <div className='text-xs text-gray-400'>
            Puntos: {points.length.toLocaleString()}
          </div>
        </div>
      </div>

      <Canvas
        shadows
        camera={{
          position: [0, 0, 0],
          fov: 75,
          near: 0.1,
          far: 10000,
        }}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
          preserveDrawingBuffer: true,
        }}
        dpr={[1, 2]}
      >
        {/* Fondo y efectos */}
        <color attach='background' args={['#0a0a0f']} />
        <fog attach='fog' args={['#0a0a0f', 0, 12000]} />

        {/* Iluminación */}
        <ambientLight intensity={0.6} color='#4a5568' />
        <directionalLight
          position={[100, 100, 100]}
          intensity={0.8}
          color='#ffffff'
          castShadow
        />
        <directionalLight
          position={[-100, 50, -100]}
          intensity={0.4}
          color='#667eea'
        />

        {/* Controles FPS */}
        <FPSControls />

        {/* Componentes principales */}
        <AdvancedPointCloud
          points={points}
          renderMode={renderMode}
          pointSize={pointSize}
          opacity={opacity}
        />
        {showGrid && <ReferenceGrid />}
      </Canvas>

      {/* Controles adicionales */}
      <div className='absolute bottom-4 right-4 z-10'>
        <button
          onClick={() => setShowGrid(!showGrid)}
          className='bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors'
        >
          {showGrid ? 'Ocultar Grid' : 'Mostrar Grid'}
        </button>
      </div>

      {/* Información de controles FPS */}
      <div className='absolute bottom-4 left-4 z-10 bg-black/80 backdrop-blur-sm rounded-lg p-3 text-white text-xs max-w-xs'>
        <h3 className='font-semibold mb-2'>Controles FPS:</h3>
        <ul className='space-y-1 text-gray-300'>
          <li>
            • <strong>Click:</strong> Capturar mouse
          </li>
          <li>
            • <strong>WASD:</strong> Movimiento
          </li>
          <li>
            • <strong>Mouse:</strong> Mirar alrededor
          </li>
          <li>
            • <strong>Shift:</strong> Correr
          </li>
          <li>
            • <strong>Space:</strong> Subir
          </li>
          <li>
            • <strong>ESC:</strong> Liberar mouse
          </li>
        </ul>
      </div>

      {/* Crosshair */}
      <div className='absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10'>
        <div className='w-4 h-4 border border-white/50 rounded-full flex items-center justify-center'>
          <div className='w-1 h-1 bg-white/80 rounded-full'></div>
        </div>
      </div>
    </div>
  );
}
