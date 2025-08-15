'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import LidarVisualization from '@/components/lidar-visualization';

interface Point {
  i: number; // intensity
  a: number; // angle
  d: number; // distance
}

interface SensorData {
  points: Point[];
}

export default function Home() {
  const [isConnected, setIsConnected] = useState(false);
  const [points, setPoints] = useState<Point[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<
    'disconnected' | 'connecting' | 'connected' | 'error'
  >('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pointsMapRef = useRef<Map<number, Point>>(new Map());

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
          const data: SensorData = JSON.parse(event.data);
          console.log('Datos recibidos:', data);

          if (data.points && Array.isArray(data.points)) {
            data.points.forEach((newPoint) => {
              pointsMapRef.current.set(newPoint.a, newPoint);
            });

            const allPoints = Array.from(pointsMapRef.current.values());
            setPoints(allPoints);
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
    pointsMapRef.current.clear();
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Conectado';
      case 'connecting':
        return 'Conectando...';
      case 'error':
        return 'Error';
      default:
        return 'Desconectado';
    }
  };

  return (
    <div className='min-h-screen bg-background p-4'>
      <div className='max-w-7xl mx-auto space-y-6'>
        <div className='flex items-center justify-between'>
          <h1 className='text-3xl font-bold'>Visualizador LIDAR</h1>
          <div className='flex items-center gap-4'>
            <Badge className={getStatusColor()}>{getStatusText()}</Badge>
            {!isConnected ? (
              <Button
                onClick={connectWebSocket}
                disabled={connectionStatus === 'connecting'}
              >
                {connectionStatus === 'connecting'
                  ? 'Conectando...'
                  : 'Conectar'}
              </Button>
            ) : (
              <Button variant='destructive' onClick={disconnect}>
                Desconectar
              </Button>
            )}
          </div>
        </div>

        <div className='grid grid-cols-1 lg:grid-cols-4 gap-6'>
          <div className='lg:col-span-3'>
            <Card>
              <CardHeader>
                <CardTitle>Visualización 3D</CardTitle>
              </CardHeader>
              <CardContent className='p-0'>
                <div className='h-[600px] w-full'>
                  <LidarVisualization points={points} />
                </div>
              </CardContent>
            </Card>
          </div>

          <div className='space-y-4'>
            <Card>
              <CardHeader>
                <CardTitle>Estadísticas</CardTitle>
              </CardHeader>
              <CardContent className='space-y-4'>
                <div>
                  <p className='text-sm text-muted-foreground'>
                    Puntos detectados
                  </p>
                  <p className='text-2xl font-bold'>{points.length}</p>
                </div>

                <div>
                  <p className='text-sm text-muted-foreground'>
                    Última actualización
                  </p>
                  <p className='text-sm'>
                    {lastUpdate ? lastUpdate.toLocaleTimeString() : 'N/A'}
                  </p>
                </div>

                {points.length > 0 && (
                  <>
                    <div>
                      <p className='text-sm text-muted-foreground'>
                        Distancia promedio
                      </p>
                      <p className='text-lg font-semibold'>
                        {(
                          points.reduce((sum, p) => sum + p.d, 0) /
                          points.length
                        ).toFixed(1)}{' '}
                        cm
                      </p>
                    </div>

                    <div>
                      <p className='text-sm text-muted-foreground'>
                        Intensidad promedio
                      </p>
                      <p className='text-lg font-semibold'>
                        {(
                          points.reduce((sum, p) => sum + p.i, 0) /
                          points.length
                        ).toFixed(0)}
                      </p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Configuración</CardTitle>
              </CardHeader>
              <CardContent className='space-y-2'>
                <div>
                  <p className='text-sm text-muted-foreground'>
                    Servidor WebSocket
                  </p>
                  <p className='text-sm font-mono'>ws://localhost:3000</p>
                </div>
                <div>
                  <p className='text-sm text-muted-foreground'>Estado</p>
                  <p className='text-sm'>{getStatusText()}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
