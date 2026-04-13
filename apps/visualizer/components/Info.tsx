import React, { useRef } from 'react';
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

interface InfoProps {
  connectionStatus: string;
  isConnected: boolean;
  points: any[];
  lastUpdate: Date | null;
  connect: () => void;
  disconnect: () => void;
  exportData: () => void;
  importData: (file: File) => void;
  importFromURL: (url: string) => void;
  clearScan: () => void;
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
}: InfoProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

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
          <DropdownItem
            key="t3-210"
            description="Facultad de Ingeniería USAC"
            onClick={() =>
              importFromURL(
                'https://pub-4fbb31ff60a64dc0a85d1af67478682f.r2.dev/test-file/t3-210.json'
              )
            }
          >
            Salón T3-210
          </DropdownItem>
          <DropdownItem
            key="dataset-01"
            description="TF-Mini S · φ 0°–60° · 11,041 pts"
            onClick={() =>
              importFromURL(
                'https://pub-4fbb31ff60a64dc0a85d1af67478682f.r2.dev/datasets/dataset-01.json'
              )
            }
          >
            Dataset 01
          </DropdownItem>
          <DropdownItem
            key="dataset-02"
            description="TF-Mini S · φ 65°–120° · 9,799 pts"
            onClick={() =>
              importFromURL(
                'https://pub-4fbb31ff60a64dc0a85d1af67478682f.r2.dev/datasets/dataset-02.json'
              )
            }
          >
            Dataset 02
          </DropdownItem>
          <DropdownItem
            key="dataset-03"
            description="TF-Mini S · φ 26°–120° · 16,659 pts"
            onClick={() =>
              importFromURL(
                'https://pub-4fbb31ff60a64dc0a85d1af67478682f.r2.dev/datasets/dataset-03.json'
              )
            }
          >
            Dataset 03
          </DropdownItem>
          <DropdownItem
            key="dataset-04"
            description="TF-Mini S · φ 10°–120° · 19,600 pts"
            onClick={() =>
              importFromURL(
                'https://pub-4fbb31ff60a64dc0a85d1af67478682f.r2.dev/datasets/dataset-04.json'
              )
            }
          >
            Dataset 04
          </DropdownItem>
          <DropdownItem
            key="dataset-05"
            description="LD19 · 2D estático · 99 pts"
            onClick={() =>
              importFromURL(
                'https://pub-4fbb31ff60a64dc0a85d1af67478682f.r2.dev/datasets/dataset-05.json'
              )
            }
          >
            Dataset 05
          </DropdownItem>
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
                  <Button color="danger" size="sm" onClick={disconnect} fullWidth>
                    Desconectar
                  </Button>
                </div>
              </AccordionItem>

              <AccordionItem key="data" title="Datos">
                <div className="flex flex-col gap-2 pb-2">
                  <Button
                    color="warning"
                    size="sm"
                    onClick={clearScan}
                    fullWidth
                  >
                    Limpiar escaneo
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
