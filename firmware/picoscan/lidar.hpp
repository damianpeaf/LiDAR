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
bool is_valid_lidar_frame(const uint8_t *frame);
int parse_points(const uint8_t *frame, LidarPoint *points);

// Parser incremental de frames — acumula bytes y notifica cuando hay frame completo
class LidarFrameParser {
public:
    LidarFrameParser() : bytes_collected_(0) {}

    // Retorna true y copia el frame a `out_frame` cuando hay un frame válido completo
    bool push_byte(uint8_t byte, uint8_t *out_frame);
    void reset();

private:
    uint8_t frame_[FRAME_SIZE];
    int bytes_collected_;

    void resync();
};

#endif // LIDAR_HPP
