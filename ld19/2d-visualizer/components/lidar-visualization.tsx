'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface Point {
  intensity: number;
  x: number;
  y: number;
  z: number;
}

interface LidarVisualizationProps {
  points: Point[];
}

export default function LidarVisualization({
  points,
}: LidarVisualizationProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene>();
  const rendererRef = useRef<THREE.WebGLRenderer>();
  const cameraRef = useRef<THREE.PerspectiveCamera>();
  const pointsObjectRef = useRef<THREE.Points>();
  const frameRef = useRef<number>();

  useEffect(() => {
    if (!mountRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);
    sceneRef.current = scene;

    // Camera setup
    const camera = new THREE.PerspectiveCamera(
      75,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      10000
    );
    camera.position.set(0, 500, 500);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(
      mountRef.current.clientWidth,
      mountRef.current.clientHeight
    );
    renderer.setPixelRatio(window.devicePixelRatio);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Add grid helper
    const gridHelper = new THREE.GridHelper(2000, 20, 0x444444, 0x222222);
    scene.add(gridHelper);

    // Add axes helper
    const axesHelper = new THREE.AxesHelper(500);
    scene.add(axesHelper);

    // Add circular reference lines
    const circleGeometry1 = new THREE.RingGeometry(200, 202, 0, Math.PI * 2);
    const circleGeometry2 = new THREE.RingGeometry(400, 402, 0, Math.PI * 2);
    const circleGeometry3 = new THREE.RingGeometry(600, 602, 0, Math.PI * 2);

    const circleMaterial = new THREE.MeshBasicMaterial({
      color: 0x333333,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.5,
    });

    const circle1 = new THREE.Mesh(circleGeometry1, circleMaterial);
    const circle2 = new THREE.Mesh(circleGeometry2, circleMaterial);
    const circle3 = new THREE.Mesh(circleGeometry3, circleMaterial);

    circle1.rotation.x = -Math.PI / 2;
    circle2.rotation.x = -Math.PI / 2;
    circle3.rotation.x = -Math.PI / 2;

    scene.add(circle1);
    scene.add(circle2);
    scene.add(circle3);

    // Add lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);

    // Animation loop
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);

      // Rotate camera around the scene
      const time = Date.now() * 0.0005;
      camera.position.x = Math.cos(time) * 800;
      camera.position.z = Math.sin(time) * 800;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      if (!mountRef.current) return;

      camera.aspect =
        mountRef.current.clientWidth / mountRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(
        mountRef.current.clientWidth,
        mountRef.current.clientHeight
      );
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  // Update points when data changes
  useEffect(() => {
    if (!sceneRef.current || !points.length) return;

    // Remove previous points
    if (pointsObjectRef.current) {
      sceneRef.current.remove(pointsObjectRef.current);
      pointsObjectRef.current.geometry.dispose();
      if (Array.isArray(pointsObjectRef.current.material)) {
        pointsObjectRef.current.material.forEach((material) =>
          material.dispose()
        );
      } else {
        pointsObjectRef.current.material.dispose();
      }
    }

    // Use Cartesian coordinates directly
    const positions = new Float32Array(points.length * 3);
    const colors = new Float32Array(points.length * 3);

    points.forEach((point, index) => {
      // Use x, y, z directly
      positions[index * 3] = point.x;
      positions[index * 3 + 1] = point.y;
      positions[index * 3 + 2] = point.z;

      // Color based on intensity (0-255) and distance
      const intensityNorm = point.intensity / 255;
      const distanceNorm = Math.min(
        Math.sqrt(point.x ** 2 + point.y ** 2 + point.z ** 2) / 1000,
        1
      ); // Normalize distance to 0-1

      // Create color gradient: close = red, medium = yellow, far = blue
      // High intensity = brighter
      if (distanceNorm < 0.3) {
        // Close points - red to orange
        colors[index * 3] = 1 * intensityNorm; // R
        colors[index * 3 + 1] = 0.3 * intensityNorm; // G
        colors[index * 3 + 2] = 0; // B
      } else if (distanceNorm < 0.7) {
        // Medium points - yellow to green
        colors[index * 3] = 0.8 * intensityNorm; // R
        colors[index * 3 + 1] = 1 * intensityNorm; // G
        colors[index * 3 + 2] = 0.2 * intensityNorm; // B
      } else {
        // Far points - blue to cyan
        colors[index * 3] = 0.2 * intensityNorm; // R
        colors[index * 3 + 1] = 0.6 * intensityNorm; // G
        colors[index * 3 + 2] = 1 * intensityNorm; // B
      }
    });

    // Create geometry and material
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 8,
      vertexColors: true,
      transparent: true,
      opacity: 0.8,
      sizeAttenuation: true,
    });

    // Create points object
    const pointsObject = new THREE.Points(geometry, material);
    pointsObjectRef.current = pointsObject;
    sceneRef.current.add(pointsObject);
  }, [points]);

  return (
    <div
      ref={mountRef}
      className='w-full h-full'
      style={{ minHeight: '400px' }}
    />
  );
}
