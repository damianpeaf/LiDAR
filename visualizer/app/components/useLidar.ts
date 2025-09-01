import { useEffect, useRef, useState } from 'react';

interface Point {
  intensity: number;
  x: number;
  y: number;
  z: number;
}

const STORAGE_KEY = 'lidar_points';

export const useLidar = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [points, setPoints] = useState<Point[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<
    'disconnected' | 'connecting' | 'connected' | 'error'
  >('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // 🔹 Cargar datos almacenados al inicio
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          setPoints(parsed);
        }
      } catch (err) {
        console.error('Error al leer localStorage:', err);
      }
    }
  }, []);

  // 🔹 Guardar datos en localStorage cuando cambien
  useEffect(() => {
    if (points.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(points));
    }
  }, [points]);

  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket('ws://localhost:3000');

      ws.onopen = () => {
        console.log('Conectado al servidor WebSocket');
        setIsConnected(true);
        setConnectionStatus('connected');
        ws.send(JSON.stringify({ type: 'register', client: 'web' }));
      };

      ws.onmessage = (event) => {
        try {
          const rawData = JSON.parse(event.data);
          console.log('Datos recibidos:', rawData);

          if (Array.isArray(rawData)) {
            const newPoints: Point[] = rawData.map((p: any) => ({
              intensity: p.intensity,
              x: p.x,
              y: p.y,
              z: p.z,
            }));

            setPoints((prevPoints) => [...prevPoints, ...newPoints]);
            setLastUpdate(new Date());
          }
        } catch (error) {
          console.error('Error al parsear datos:', error);
        }
      };

      ws.onclose = () => {
        console.log('Conexión WebSocket cerrada');
        setIsConnected(false);
        setConnectionStatus('disconnected');
        wsRef.current = null;
      };

      ws.onerror = (error) => {
        console.error('Error WebSocket:', error);
        setConnectionStatus('error');
        setIsConnected(false);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error al conectar:', error);
      setConnectionStatus('error');
    }
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setConnectionStatus('disconnected');
    setPoints([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    isConnected,
    points,
    connectionStatus,
    lastUpdate,
    connect: connectWebSocket,
    disconnect,
  };
};
