import { useEffect, useRef, useState } from 'react';
import { addToast } from '@heroui/react';

interface Point {
  intensity: number;
  x: number;
  y: number;
  z: number;
}

interface ServerMessage {
  type: 'initial_state' | 'new_points' | 'scan_cleared' | 'clear_response';
  data?: Point[];
  success?: boolean;
}

export const useLidar = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [points, setPoints] = useState<Point[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<
    'disconnected' | 'connecting' | 'connected' | 'error'
  >('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');

    try {
      const wsProtocol =
        window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = window.location.hostname || 'localhost';
      const ws = new WebSocket(`${wsProtocol}//${wsHost}:3000`);

      ws.onopen = () => {
        console.log('Conectado al servidor WebSocket');
        setIsConnected(true);
        setConnectionStatus('connected');

        addToast({
          title: 'Conectado',
          description: 'Conexión establecida con el servidor LiDAR',
          color: 'success',
        });

        // Registrarse como cliente web
        ws.send(JSON.stringify({ type: 'register', client: 'web' }));
      };

      ws.onmessage = (event) => {
        try {
          const message: ServerMessage = JSON.parse(event.data);
          console.log('Mensaje recibido:', message);

          switch (message.type) {
            case 'initial_state':
              // Al conectarse, recibir el estado completo desde el servidor
              if (Array.isArray(message.data)) {
                setPoints(message.data);
                setLastUpdate(new Date());
                console.log(
                  `Estado inicial cargado: ${message.data.length} puntos`
                );
              }
              break;

            case 'new_points':
              // Agregar nuevos puntos a los existentes
              if (Array.isArray(message.data)) {
                setPoints((prevPoints) => [
                  ...prevPoints,
                  ...(message.data ?? []),
                ]);
                setLastUpdate(new Date());
                console.log(`Nuevos puntos agregados: ${message.data.length}`);
              }
              break;

            case 'scan_cleared':
              // Limpiar todos los puntos cuando el servidor notifica limpieza
              setPoints([]);
              setLastUpdate(new Date());
              console.log('Escaneo limpiado por otro cliente');
              addToast({
                title: 'Escaneo limpiado',
                description: 'Los datos fueron limpiados por otro cliente',
                color: 'warning',
              });
              break;

            case 'clear_response':
              // Respuesta a nuestra solicitud de limpieza
              setIsClearing(false);
              if (message.success) {
                console.log('Escaneo limpiado exitosamente');
                addToast({
                  title: 'Escaneo limpiado',
                  description: 'Todos los puntos han sido eliminados',
                  color: 'success',
                });
              } else {
                console.error('Error al limpiar escaneo');
                addToast({
                  title: 'Error al limpiar',
                  description: 'No se pudo limpiar el escaneo',
                  color: 'danger',
                });
              }
              break;

            default:
              console.warn('Tipo de mensaje desconocido:', message.type);
          }
        } catch (error) {
          console.error('Error al parsear mensaje del servidor:', error);

          // Fallback para compatibilidad con formato anterior
          try {
            const rawData = JSON.parse(event.data);
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
          } catch (fallbackError) {
            console.error('Error en fallback de parsing:', fallbackError);
          }
        }
      };

      ws.onclose = () => {
        console.log('Conexión WebSocket cerrada');
        setIsConnected(false);
        setConnectionStatus('disconnected');
        setIsClearing(false);
        wsRef.current = null;

        addToast({
          title: 'Desconectado',
          description: 'La conexión con el servidor se ha cerrado',
          color: 'default',
        });
      };

      ws.onerror = (error) => {
        console.error('Error WebSocket:', error);
        setConnectionStatus('error');
        setIsConnected(false);
        setIsClearing(false);

        addToast({
          title: 'Error de conexión',
          description: 'No se pudo establecer conexión con el servidor',
          color: 'danger',
        });
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error al conectar:', error);
      setConnectionStatus('error');

      addToast({
        title: 'Error',
        description: 'Ocurrió un error al intentar conectar',
        color: 'danger',
      });
    }
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setConnectionStatus('disconnected');
    setIsClearing(false);
    // No limpiar puntos localmente al desconectar,
    // ya que el estado persistirá en el servidor
  };

  const clearScan = () => {
    if (!isConnected || !wsRef.current || isClearing) {
      console.warn('No se puede limpiar: no conectado o ya limpiando');
      addToast({
        title: 'No disponible',
        description: 'Debes estar conectado para limpiar el escaneo',
        color: 'warning',
      });
      return;
    }

    setIsClearing(true);

    try {
      wsRef.current.send(JSON.stringify({ type: 'clear_scan' }));
      console.log('Solicitud de limpieza enviada');
    } catch (error) {
      console.error('Error al enviar solicitud de limpieza:', error);
      setIsClearing(false);
      addToast({
        title: 'Error',
        description: 'No se pudo enviar la solicitud de limpieza',
        color: 'danger',
      });
    }
  };

  // Cleanup al desmontar el componente
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const exportData = () => {
    try {
      const dataStr =
        'data:text/json;charset=utf-8,' +
        encodeURIComponent(JSON.stringify(points));

      const link = document.createElement('a');
      link.href = dataStr;
      link.download = 'lidar_data.json';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      addToast({
        title: 'Datos exportados',
        description: `${points.length} puntos exportados exitosamente`,
        color: 'success',
      });
    } catch (error) {
      console.error('Error al exportar datos:', error);
      addToast({
        title: 'Error al exportar',
        description: 'No se pudieron exportar los datos',
        color: 'danger',
      });
    }
  };

  const importData = (file: File) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const importedPoints: Point[] = JSON.parse(
          event.target?.result as string
        );
        setPoints((prevPoints) => [...prevPoints, ...importedPoints]);
        setLastUpdate(new Date());
        console.log(`Puntos importados: ${importedPoints.length}`);

        addToast({
          title: 'Datos importados',
          description: `${importedPoints.length} puntos importados desde ${file.name}`,
          color: 'success',
        });
      } catch (error) {
        console.error('Error al importar datos:', error);
        addToast({
          title: 'Error al importar',
          description: 'El archivo no tiene un formato válido',
          color: 'danger',
        });
      }
    };

    reader.onerror = () => {
      addToast({
        title: 'Error de lectura',
        description: 'No se pudo leer el archivo',
        color: 'danger',
      });
    };

    reader.readAsText(file);
  };

  const importFromURL = async (url: string) => {
    try {
      addToast({
        title: 'Descargando',
        description: 'Cargando datos desde el servidor...',
        color: 'primary',
      });

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Error al descargar archivo: ${response.status}`);
      }
      const importedPoints: Point[] = await response.json();
      setPoints((prevPoints) => [...prevPoints, ...importedPoints]);
      setLastUpdate(new Date());
      console.log(`Puntos importados desde URL: ${importedPoints.length}`);

      addToast({
        title: 'Ejemplo cargado',
        description: `${importedPoints.length} puntos importados exitosamente`,
        color: 'success',
      });
    } catch (error) {
      console.error('Error al importar datos desde URL:', error);
      addToast({
        title: 'Error al cargar',
        description: 'No se pudo descargar el archivo de ejemplo',
        color: 'danger',
      });
    }
  };

  return {
    isConnected,
    points,
    connectionStatus,
    lastUpdate,
    isClearing,
    connect: connectWebSocket,
    disconnect,
    clearScan,
    exportData,
    importData,
    importFromURL,
  };
};
