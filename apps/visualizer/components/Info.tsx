import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
  Button,
  Chip,
  Divider,
  Accordion,
  AccordionItem,
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
} from '@heroui/react';
import Link from 'next/link';

import { createClient } from '../lib/supabase/client';

interface ExampleRecord {
  id: string;
  name: string;
  description: string | null;
  r2_url: string;
}

interface InfoProps {
  connectionStatus: string;
  isConnected: boolean;
  points: any[];
  lastUpdate: Date | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  exportData: () => void;
  importData: (file: File) => void;
  importFromURL: (url: string) => void;
  clearScan: () => void;
  saveScan: () => void;
  isSaving: boolean;
  canUseLiveFeatures: boolean;
  currentUserEmail: string | null;
  signOut: () => Promise<void>;
}

export const Info = ({
  connectionStatus,
  isConnected,
  points,
  lastUpdate,
  connect,
  disconnect,
  exportData,
  importData,
  importFromURL,
  clearScan,
  saveScan,
  isSaving,
  canUseLiveFeatures,
  currentUserEmail,
  signOut,
}: InfoProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [examples, setExamples] = useState<ExampleRecord[]>([]);
  const [isLoadingExamples, setIsLoadingExamples] = useState(true);
  const [examplesError, setExamplesError] = useState<string | null>(null);

  const loadExamples = useCallback(async () => {
    try {
      setIsLoadingExamples(true);
      setExamplesError(null);

      const supabase = createClient();
      const { data, error } = await supabase
        .from('examples')
        .select('id, name, description, r2_url')
        .order('created_at', { ascending: false });

      if (error) {
        throw error;
      }

      setExamples(data ?? []);
    } catch (error) {
      console.error('Error cargando ejemplos desde Supabase:', error);
      setExamples([]);
      setExamplesError('No se pudieron cargar los ejemplos');
    } finally {
      setIsLoadingExamples(false);
    }
  }, []);

  useEffect(() => {
    void loadExamples();
  }, [loadExamples, canUseLiveFeatures, currentUserEmail]);

  return (
    <div className="absolute top-4 left-4 z-50 flex items-center gap-2">
      {/* Stats badge - always visible */}
      <Chip
        color={isConnected ? 'success' : 'default'}
        variant="flat"
        size="sm"
      >
        {points.length.toLocaleString()} pts
      </Chip>

      {/* Examples dropdown - directly accessible */}
      <Dropdown placement="bottom-start">
        <DropdownTrigger>
          <Button size="sm" variant="flat" color="primary">
            Ejemplos
          </Button>
        </DropdownTrigger>
        <DropdownMenu aria-label="Ejemplos de escaneos">
          {isLoadingExamples ? (
            <DropdownItem key="examples-loading" isDisabled>
              Cargando ejemplos...
            </DropdownItem>
          ) : examplesError ? (
            <DropdownItem
              key="examples-error"
              description="Tocá para reintentar"
              onClick={() => {
                void loadExamples();
              }}
            >
              {examplesError}
            </DropdownItem>
          ) : examples.length === 0 ? (
            <DropdownItem key="examples-empty" isDisabled>
              No hay ejemplos disponibles
            </DropdownItem>
          ) : (
            examples.map((example) => (
              <DropdownItem
                key={example.id}
                description={example.description ?? 'Sin descripción'}
                onClick={() => importFromURL(example.r2_url)}
              >
                {example.name}
              </DropdownItem>
            ))
          )}
        </DropdownMenu>
      </Dropdown>

      {/* Menu popover */}
      <Popover placement="bottom-start" showArrow>
        <PopoverTrigger>
          <Button isIconOnly size="sm" variant="flat">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-5 h-5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
              />
            </svg>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[300px]">
          <div className="px-1 py-2 w-full">
            <div className="text-small font-bold mb-2">LiDAR Visualizer</div>

            <Button
              as={Link}
              href="/"
              size="sm"
              variant="flat"
              className="w-full mb-3"
            >
              Volver al inicio
            </Button>

            <div className="flex justify-between text-xs mb-2">
              <span className="text-default-500">Usuario:</span>
              <span className="text-xs max-w-[170px] truncate" title={currentUserEmail ?? 'Anónimo'}>
                {currentUserEmail ?? 'Anónimo'}
              </span>
            </div>

            {currentUserEmail && (
              <Button
                size="sm"
                variant="light"
                color="danger"
                onClick={signOut}
                className="w-full mb-3"
              >
                Cerrar sesión
              </Button>
            )}

            <div className="flex justify-between text-xs mb-3">
              <span className="text-default-500">Estado:</span>
              <Chip color={isConnected ? 'success' : 'default'} size="sm">
                {connectionStatus}
              </Chip>
            </div>

            <div className="flex justify-between text-xs mb-3">
              <span className="text-default-500">Última actualización:</span>
              <span className="text-xs">
                {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : '—'}
              </span>
            </div>

            <Divider className="my-2" />

            <Accordion isCompact>
              <AccordionItem key="connection" title="Conexión">
                <div className="flex gap-2 pb-2">
                  <Button color="success" size="sm" onClick={connect} fullWidth>
                    Conectar
                  </Button>
                  <Button
                    color="danger"
                    size="sm"
                    onClick={disconnect}
                    isDisabled={!canUseLiveFeatures}
                    fullWidth
                  >
                    Desconectar
                  </Button>
                </div>
                {!canUseLiveFeatures && (
                  <p className="text-xs text-default-500 mt-1">
                    Modo público: funciones en vivo deshabilitadas.
                  </p>
                )}
              </AccordionItem>

              <AccordionItem key="data" title="Datos">
                <div className="flex flex-col gap-2 pb-2">
                  <Button
                    color="warning"
                    size="sm"
                    onClick={clearScan}
                    isDisabled={!canUseLiveFeatures}
                    fullWidth
                  >
                    Limpiar escaneo
                  </Button>
                  <Button
                    color="secondary"
                    size="sm"
                    onClick={saveScan}
                    isLoading={isSaving}
                    isDisabled={!canUseLiveFeatures}
                    fullWidth
                  >
                    Guardar escaneo
                  </Button>
                  <Button
                    color="primary"
                    size="sm"
                    onClick={exportData}
                    fullWidth
                  >
                    Exportar JSON
                  </Button>
                  <Button
                    color="default"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    fullWidth
                  >
                    Importar archivo
                  </Button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="application/json"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        importData(e.target.files[0]);
                      }
                    }}
                    className="hidden"
                  />
                </div>
              </AccordionItem>
            </Accordion>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
};
