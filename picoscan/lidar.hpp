#ifndef LIDAR_HPP
#define LIDAR_HPP

#include <cstdint>
#include <cstddef>
#include <cmath>

// Constantes LIDAR
constexpr uint8_t HEADER = 0x54;
constexpr int POINT_PER_PACK = 12;
constexpr int FRAME_SIZE = 47;

// Estructura para un punto LIDAR
struct LidarPoint
{
    float angle;
    uint16_t distance;
    uint8_t intensity;
    bool valid;
};

// Funciones de LIDAR
uint8_t calc_crc8(const uint8_t *data, size_t len);
int parse_points(const uint8_t *frame, LidarPoint *points);

#endif // LIDAR_HPP
