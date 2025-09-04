# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

### Building the Project
```bash
mkdir -p build
cd build
cmake ..
make
```

### Flashing to Pico W
After building, flash the generated `picoscan.uf2` file to the Raspberry Pi Pico W by:
1. Hold BOOTSEL button while connecting USB
2. Copy `build/picoscan.uf2` to the mounted RPI-RP2 drive

## Architecture Overview

This is a **LiDAR scanning system** built for Raspberry Pi Pico W that performs 3D environmental scanning by combining:

### Core Components

1. **LiDAR Data Processing** (`lidar.hpp/cpp`)
   - Parses UART frames from LiDAR sensor (47-byte frames, 12 points per packet)
   - Handles CRC validation and point extraction
   - Each point contains: angle (0-360°), distance (mm), intensity (0-255)

2. **Servo Control System** (`picoscan.cpp:77-166`)
   - Controls precision servo motor for vertical scanning axis
   - High-resolution positioning (5μs steps, 500-2500μs pulse range)
   - Automatic sweep pattern with sample collection at each position
   - Waits for complete LiDAR rotations before moving to next position

3. **Network Communication** (`picoscan.cpp:168-291`, `ws.h/cpp`)
   - TCP client connecting to remote server (192.168.1.24:3000)
   - WebSocket protocol implementation for real-time data streaming
   - Batched point transmission (100 points per message)

4. **UART Utilities** (`uart_utils.hpp/cpp`)
   - Timeout-based UART reading functions
   - Buffer management for reliable LiDAR communication

### Data Flow

1. **Initialization**: WiFi connection → TCP/WebSocket handshake → servo positioning
2. **Scanning Loop**:
   - Read LiDAR UART frames (230400 baud)
   - Parse and validate points
   - Wait for complete 360° LiDAR rotation
   - Collect multiple samples per servo position
   - Move servo to next position when sampling complete
3. **Data Transmission**: Batch points by servo angle and stream via WebSocket

### Key Configuration

- **LiDAR**: UART1 (pins 8,9) at 230400 baud
- **Servo**: PWM on pin 15, 20ms period
- **WiFi**: Configured for specific network (credentials in picoscan.cpp:312-313)
- **Sampling**: 2 samples per servo position, 5000+ points per complete rotation
- **Network**: TCP port 3000, WebSocket text frames

### Hardware Requirements

- Raspberry Pi Pico W
- LiDAR sensor with UART output (compatible with 47-byte frame format)
- Precision servo motor
- Stable power supply for both Pico and servo

The system creates detailed 3D point clouds by combining horizontal LiDAR scanning with precise vertical servo positioning.