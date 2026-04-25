from machine import Pin, UART
import gc
import struct
import time


UART_ID = 1
UART_BAUD = 230400
UART_TX_PIN = 8
UART_RX_PIN = 9

HEADER = 0x54
POINT_PER_PACK = 12
FRAME_SIZE = 47
BENCHMARK_DURATION_MS = 60000
UART_DRAIN_CHUNK_SIZE = 128

uart = UART(UART_ID, UART_BAUD, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))

CRC_TABLE = [
    0x00, 0x4d, 0x9a, 0xd7, 0x79, 0x34, 0xe3, 0xae, 0xf2, 0xbf, 0x68, 0x25, 0x8b, 0xc6, 0x11, 0x5c,
    0xa9, 0xe4, 0x33, 0x7e, 0xd0, 0x9d, 0x4a, 0x07, 0x5b, 0x16, 0xc1, 0x8c, 0x22, 0x6f, 0xb8, 0xf5,
    0x1f, 0x52, 0x85, 0xc8, 0x66, 0x2b, 0xfc, 0xb1, 0xed, 0xa0, 0x77, 0x3a, 0x94, 0xd9, 0x0e, 0x43,
    0xb6, 0xfb, 0x2c, 0x61, 0xcf, 0x82, 0x55, 0x18, 0x44, 0x09, 0xde, 0x93, 0x3d, 0x70, 0xa7, 0xea,
    0x3e, 0x73, 0xa4, 0xe9, 0x47, 0x0a, 0xdd, 0x90, 0xcc, 0x81, 0x56, 0x1b, 0xb5, 0xf8, 0x2f, 0x62,
    0x97, 0xda, 0x0d, 0x40, 0xee, 0xa3, 0x74, 0x39, 0x65, 0x28, 0xff, 0xb2, 0x1c, 0x51, 0x86, 0xcb,
    0x21, 0x6c, 0xbb, 0xf6, 0x58, 0x15, 0xc2, 0x8f, 0xd3, 0x9e, 0x49, 0x04, 0xaa, 0xe7, 0x30, 0x7d,
    0x88, 0xc5, 0x12, 0x5f, 0xf1, 0xbc, 0x6b, 0x26, 0x7a, 0x37, 0xe0, 0xad, 0x03, 0x4e, 0x99, 0xd4,
    0x7c, 0x31, 0xe6, 0xab, 0x05, 0x48, 0x9f, 0xd2, 0x8e, 0xc3, 0x14, 0x59, 0xf7, 0xba, 0x6d, 0x20,
    0xd5, 0x98, 0x4f, 0x02, 0xac, 0xe1, 0x36, 0x7b, 0x27, 0x6a, 0xbd, 0xf0, 0x5e, 0x13, 0xc4, 0x89,
    0x63, 0x2e, 0xf9, 0xb4, 0x1a, 0x57, 0x80, 0xcd, 0x91, 0xdc, 0x0b, 0x46, 0xe8, 0xa5, 0x72, 0x3f,
    0xca, 0x87, 0x50, 0x1d, 0xb3, 0xfe, 0x29, 0x64, 0x38, 0x75, 0xa2, 0xef, 0x41, 0x0c, 0xdb, 0x96,
    0x42, 0x0f, 0xd8, 0x95, 0x3b, 0x76, 0xa1, 0xec, 0xb0, 0xfd, 0x2a, 0x67, 0xc9, 0x84, 0x53, 0x1e,
    0xeb, 0xa6, 0x71, 0x3c, 0x92, 0xdf, 0x08, 0x45, 0x19, 0x54, 0x83, 0xce, 0x60, 0x2d, 0xfa, 0xb7,
    0x5d, 0x10, 0xc7, 0x8a, 0x24, 0x69, 0xbe, 0xf3, 0xaf, 0xe2, 0x35, 0x78, 0xd6, 0x9b, 0x4c, 0x01,
    0xf4, 0xb9, 0x6e, 0x23, 0x8d, 0xc0, 0x17, 0x5a, 0x06, 0x4b, 0x9c, 0xd1, 0x7f, 0x32, 0xe5, 0xa8,
]


class Stats:
    def __init__(self):
        self.start_ms = 0
        self.last_periodic_ms = 0
        self.bytes_received = 0
        self.bytes_processed = 0
        self.frames_received = 0
        self.frames_valid = 0
        self.frames_crc_error = 0
        self.frames_header_error = 0
        self.frames_size_error = 0
        self.header_miss_count = 0
        self.points_total = 0
        self.total_frame_time_us = 0
        self.total_parse_time_us = 0
        self.total_crc_time_us = 0
        self.total_uart_read_time_us = 0
        self.min_frame_time_us = 0
        self.max_frame_time_us = 0
        self.ram_free_start = 0
        self.ram_free_end = 0


stats = Stats()


def emit(component, event, extra=""):
    line = "EXP|ts_us={}|profile=benchmark|component={}|event={}".format(
        time.ticks_us(), component, event
    )
    if extra:
        line += "|" + extra
    print(line)


def safe_divide(numerator, denominator):
    if denominator <= 0:
        return 0
    return numerator / denominator


def calc_crc8(data):
    crc = 0
    for byte in data:
        crc = CRC_TABLE[(crc ^ byte) & 0xFF]
    return crc


def normalize_angle(angle):
    angle_deg = angle / 100.0
    while angle_deg < 0:
        angle_deg += 360
    while angle_deg >= 360:
        angle_deg -= 360
    return angle_deg


def parse_lidar_frame(data):
    parse_start_us = time.ticks_us()

    if len(data) != FRAME_SIZE:
        stats.frames_size_error += 1
        return 0, 0

    if data[0] != HEADER:
        stats.frames_header_error += 1
        return 0, 0

    crc_start_us = time.ticks_us()
    crc_ok = calc_crc8(data[:-1]) == data[-1]
    crc_elapsed_us = time.ticks_diff(time.ticks_us(), crc_start_us)
    stats.total_crc_time_us += crc_elapsed_us
    if not crc_ok:
        stats.frames_crc_error += 1
        return 0, crc_elapsed_us

    start_angle = struct.unpack("<H", data[4:6])[0]
    end_angle = struct.unpack("<H", data[42:44])[0]
    start_angle_norm = normalize_angle(start_angle)
    end_angle_norm = normalize_angle(end_angle)

    if end_angle_norm < start_angle_norm:
        end_angle_norm += 360

    step = (end_angle_norm - start_angle_norm) / (POINT_PER_PACK - 1)
    points_data = data[6:42]
    valid_points = 0

    for i in range(POINT_PER_PACK):
        offset = i * 3
        distance, _intensity = struct.unpack("<HB", points_data[offset:offset + 3])
        _angle = start_angle_norm + step * i
        if distance > 0:
            valid_points += 1

    stats.total_parse_time_us += time.ticks_diff(time.ticks_us(), parse_start_us)
    return valid_points, crc_elapsed_us


def elapsed_s(now_ms=None):
    if now_ms is None:
        now_ms = time.ticks_ms()
    return time.ticks_diff(now_ms, stats.start_ms) / 1000.0


def avg(value, count):
    return int(safe_divide(value, count))


def emit_stats(event, reason=""):
    now_ms = time.ticks_ms()
    duration_s = elapsed_s(now_ms)
    frame_errors = stats.frames_crc_error + stats.frames_header_error + stats.frames_size_error
    error_rate = safe_divide(frame_errors * 100.0, stats.frames_received)
    success_rate = safe_divide(stats.frames_valid * 100.0, stats.frames_received)
    avg_frame_time = avg(stats.total_frame_time_us, stats.frames_valid)
    avg_parse_time = avg(stats.total_parse_time_us, stats.frames_valid)
    avg_crc_time = avg(stats.total_crc_time_us, stats.frames_received)
    avg_uart_read_time = avg(stats.total_uart_read_time_us, stats.frames_received)

    parts = []
    if reason:
        parts.append("reason={}".format(reason))
    parts.extend([
        "duration_s={:.3f}".format(duration_s),
        "bytes_received={}".format(stats.bytes_received),
        "bytes_processed={}".format(stats.bytes_processed),
        "frames_received={}".format(stats.frames_received),
        "frames_valid={}".format(stats.frames_valid),
        "frames_crc_error={}".format(stats.frames_crc_error),
        "frames_header_error={}".format(stats.frames_header_error),
        "frames_size_error={}".format(stats.frames_size_error),
        "header_miss_count={}".format(stats.header_miss_count),
        "points_total={}".format(stats.points_total),
        "frames_per_s={:.3f}".format(safe_divide(stats.frames_valid, duration_s)),
        "points_per_s={:.3f}".format(safe_divide(stats.points_total, duration_s)),
        "bytes_per_s={:.3f}".format(safe_divide(stats.bytes_received, duration_s)),
        "avg_frame_time_us={}".format(avg_frame_time),
        "min_frame_time_us={}".format(stats.min_frame_time_us),
        "max_frame_time_us={}".format(stats.max_frame_time_us),
        "avg_parse_time_us={}".format(avg_parse_time),
        "avg_crc_time_us={}".format(avg_crc_time),
        "avg_uart_read_time_us={}".format(avg_uart_read_time),
        "success_rate_pct={:.3f}".format(success_rate),
        "error_rate_pct={:.3f}".format(error_rate),
        "ram_free_start={}".format(stats.ram_free_start),
        "ram_free_end={}".format(gc.mem_free()),
    ])
    emit("telemetry", event, "|".join(parts))


def find_header():
    while True:
        uart_start_us = time.ticks_us()
        byte = uart.read(1)
        stats.total_uart_read_time_us += time.ticks_diff(time.ticks_us(), uart_start_us)

        if byte:
            stats.bytes_received += 1
            if byte[0] == HEADER:
                return True
            stats.header_miss_count += 1


def drain_uart():
    while uart.any():
        pending = uart.any()
        if pending > UART_DRAIN_CHUNK_SIZE:
            pending = UART_DRAIN_CHUNK_SIZE
        uart.read(pending)


def main():
    gc.collect()
    stats.ram_free_start = gc.mem_free()
    drain_uart()
    gc.collect()
    stats.start_ms = time.ticks_ms()
    stats.last_periodic_ms = stats.start_ms

    emit("telemetry", "session_start", "schema=1|firmware=micropython_ld19|target_duration_s=60|network_enabled=0|servo_enabled=0")

    while time.ticks_diff(time.ticks_ms(), stats.start_ms) < BENCHMARK_DURATION_MS:
        frame_start_us = time.ticks_us()

        if not find_header():
            continue

        uart_start_us = time.ticks_us()
        remaining = uart.read(FRAME_SIZE - 1)
        stats.total_uart_read_time_us += time.ticks_diff(time.ticks_us(), uart_start_us)

        if not remaining or len(remaining) != FRAME_SIZE - 1:
            stats.frames_size_error += 1
            continue

        frame = bytes([HEADER]) + remaining
        stats.bytes_received += len(remaining)
        stats.bytes_processed += FRAME_SIZE
        stats.frames_received += 1

        valid_points, _crc_time = parse_lidar_frame(frame)
        if valid_points > 0:
            stats.frames_valid += 1
            stats.points_total += valid_points

            frame_time = time.ticks_diff(time.ticks_us(), frame_start_us)
            stats.total_frame_time_us += frame_time
            if stats.frames_valid == 1 or frame_time < stats.min_frame_time_us:
                stats.min_frame_time_us = frame_time
            if frame_time > stats.max_frame_time_us:
                stats.max_frame_time_us = frame_time

        now_ms = time.ticks_ms()
        if time.ticks_diff(now_ms, stats.last_periodic_ms) >= 1000:
            stats.last_periodic_ms = now_ms
            emit_stats("stats")

    gc.collect()
    stats.ram_free_end = gc.mem_free()
    emit_stats("summary", "duration_reached")
    emit("telemetry", "done", "reason=duration_reached")


if __name__ == "__main__":
    main()
