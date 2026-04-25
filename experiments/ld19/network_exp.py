from machine import Pin, PWM, UART
import gc
import network
import socket
import struct
import time
import ujson
import urandom


UART_ID = 1
UART_BAUD = 230400
UART_TX_PIN = 8
UART_RX_PIN = 9
SERVO_PIN = 15

SSID = "CLARO1_8E2AAB"
PASSWORD = ""
SERVER_HOST = "192.168.1.31"
SERVER_PORT = 3000
WEBSOCKET_PATH = "/"

HEADER = 0x54
POINT_PER_PACK = 12
FRAME_SIZE = 47
NETWORK_DURATION_MS = 60000
UART_DRAIN_CHUNK_SIZE = 128
SERVO_MIN_PULSE_US = 500
SERVO_MAX_PULSE_US = 2500
SERVO_STEP_US = 10
SERVO_SETTLE_MS = 200
SAMPLES_PER_POSITION = 3
MIN_POINTS_PER_SAMPLE = 500
SOCKET_SEND_TIMEOUT_S = 2
WS_RECONNECT_RETRIES = 3
WS_RECONNECT_BACKOFF_MS = 500
WS_RECONNECT_TRIGGER_FAILS = 5

uart = UART(UART_ID, UART_BAUD, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))


class ServoSweep:
    def __init__(self, pin):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(50)
        self.current_pulse = SERVO_MIN_PULSE_US
        self.direction = 1
        self.samples_collected = 0
        self.points_in_sample = 0
        self.sweep_passes = 0
        self.sweep_cycles = 0
        self.last_lidar_angle = -1.0
        self.waiting_for_rotation = False
        self.settling_until_ms = 0

    def angle(self):
        return (self.current_pulse - SERVO_MIN_PULSE_US) * 180.0 / (SERVO_MAX_PULSE_US - SERVO_MIN_PULSE_US)

    def set_pulse(self, pulse_us):
        duty = int(pulse_us * 65535 / 20000)
        self.pwm.duty_u16(duty)

    def init(self):
        self.set_pulse(self.current_pulse)
        self.settling_until_ms = time.ticks_add(time.ticks_ms(), SERVO_SETTLE_MS)

    def ready(self):
        return time.ticks_diff(time.ticks_ms(), self.settling_until_ms) >= 0

    def update_rotation(self, current_angle):
        if not self.ready():
            return False

        if not self.waiting_for_rotation:
            self.waiting_for_rotation = True
            self.last_lidar_angle = current_angle
            self.points_in_sample = 1
            return False

        self.points_in_sample += 1
        if self.points_in_sample < MIN_POINTS_PER_SAMPLE:
            return False

        angle_diff = abs(current_angle - self.last_lidar_angle)
        if angle_diff < 10.0 or angle_diff > 350.0:
            self.samples_collected += 1
            self.points_in_sample = 0
            self.waiting_for_rotation = False
            return True

        return False

    def should_move(self):
        return self.ready() and self.samples_collected >= SAMPLES_PER_POSITION

    def move_next(self):
        self.current_pulse += self.direction * SERVO_STEP_US

        if self.current_pulse >= SERVO_MAX_PULSE_US:
            self.current_pulse = SERVO_MAX_PULSE_US
            self.direction = -1
            self.sweep_passes += 1
        elif self.current_pulse <= SERVO_MIN_PULSE_US:
            self.current_pulse = SERVO_MIN_PULSE_US
            self.direction = 1
            self.sweep_passes += 1
            self.sweep_cycles += 1

        self.samples_collected = 0
        self.points_in_sample = 0
        self.waiting_for_rotation = False
        self.last_lidar_angle = -1.0
        self.set_pulse(self.current_pulse)
        self.settling_until_ms = time.ticks_add(time.ticks_ms(), SERVO_SETTLE_MS)

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
        self.payload_bytes_sent = 0
        self.websocket_frame_bytes_sent = 0
        self.messages_sent = 0
        self.send_failures = 0
        self.wifi_connect_ms = 0
        self.websocket_connect_ms = 0
        self.wifi_connected = 0
        self.websocket_connected = 0
        self.websocket_reconnects = 0
        self.websocket_reconnect_failures = 0
        self.consecutive_send_failures = 0
        self.samples_completed = 0
        self.servo_moves = 0
        self.sweep_passes = 0
        self.sweep_cycles = 0
        self.servo_deg = 0.0
        self.total_frame_time_us = 0
        self.total_parse_time_us = 0
        self.total_crc_time_us = 0
        self.total_send_time_us = 0
        self.min_frame_time_us = 0
        self.max_frame_time_us = 0
        self.ram_free_start = 0


stats = Stats()


def emit(component, event, extra=""):
    line = "EXP|ts_us={}|profile=network|component={}|event={}".format(
        time.ticks_us(), component, event
    )
    if extra:
        line += "|" + extra
    print(line)


def safe_divide(numerator, denominator):
    if denominator <= 0:
        return 0
    return numerator / denominator


def avg(value, count):
    return int(safe_divide(value, count))


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


def estimate_client_ws_frame_bytes(payload_len):
    if payload_len <= 125:
        header_len = 2
    elif payload_len <= 65535:
        header_len = 4
    else:
        header_len = 10
    return payload_len + header_len + 4


def parse_lidar_points(data):
    parse_start_us = time.ticks_us()

    if len(data) != FRAME_SIZE:
        stats.frames_size_error += 1
        return None

    if data[0] != HEADER:
        stats.frames_header_error += 1
        return None

    crc_start_us = time.ticks_us()
    crc_ok = calc_crc8(data[:-1]) == data[-1]
    stats.total_crc_time_us += time.ticks_diff(time.ticks_us(), crc_start_us)
    if not crc_ok:
        stats.frames_crc_error += 1
        return None

    start_angle = struct.unpack("<H", data[4:6])[0]
    end_angle = struct.unpack("<H", data[42:44])[0]
    start_angle_norm = normalize_angle(start_angle)
    end_angle_norm = normalize_angle(end_angle)

    if end_angle_norm < start_angle_norm:
        end_angle_norm += 360

    step = (end_angle_norm - start_angle_norm) / (POINT_PER_PACK - 1)
    points_data = data[6:42]
    points = []

    for i in range(POINT_PER_PACK):
        offset = i * 3
        distance, intensity = struct.unpack("<HB", points_data[offset:offset + 3])
        angle = start_angle_norm + step * i
        if angle >= 360:
            angle -= 360
        if distance > 0:
            points.append({"a": round(angle, 1), "d": distance, "i": intensity})

    stats.total_parse_time_us += time.ticks_diff(time.ticks_us(), parse_start_us)
    return points


def elapsed_s(now_ms=None):
    if stats.start_ms == 0:
        return 0.0
    if now_ms is None:
        now_ms = time.ticks_ms()
    return time.ticks_diff(now_ms, stats.start_ms) / 1000.0


def emit_stats(event, reason=""):
    duration_s = elapsed_s()
    frame_errors = stats.frames_crc_error + stats.frames_header_error + stats.frames_size_error
    success_rate = safe_divide(stats.frames_valid * 100.0, stats.frames_received)
    error_rate = safe_divide(frame_errors * 100.0, stats.frames_received)

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
        "payload_bytes_sent={}".format(stats.payload_bytes_sent),
        "payload_bytes_per_s={:.3f}".format(safe_divide(stats.payload_bytes_sent, duration_s)),
        "websocket_frame_bytes_sent={}".format(stats.websocket_frame_bytes_sent),
        "websocket_frame_bytes_per_s={:.3f}".format(safe_divide(stats.websocket_frame_bytes_sent, duration_s)),
        "avg_payload_bytes_per_message={}".format(avg(stats.payload_bytes_sent, stats.messages_sent)),
        "avg_websocket_frame_bytes_per_message={}".format(avg(stats.websocket_frame_bytes_sent, stats.messages_sent)),
        "messages_sent={}".format(stats.messages_sent),
        "send_failures={}".format(stats.send_failures),
        "avg_frame_time_us={}".format(avg(stats.total_frame_time_us, stats.frames_valid)),
        "min_frame_time_us={}".format(stats.min_frame_time_us),
        "max_frame_time_us={}".format(stats.max_frame_time_us),
        "avg_parse_time_us={}".format(avg(stats.total_parse_time_us, stats.frames_valid)),
        "avg_crc_time_us={}".format(avg(stats.total_crc_time_us, stats.frames_received)),
        "avg_send_time_us={}".format(avg(stats.total_send_time_us, stats.messages_sent)),
        "success_rate_pct={:.3f}".format(success_rate),
        "error_rate_pct={:.3f}".format(error_rate),
        "wifi_connected={}".format(stats.wifi_connected),
        "websocket_connected={}".format(stats.websocket_connected),
        "wifi_connect_ms={}".format(stats.wifi_connect_ms),
        "websocket_connect_ms={}".format(stats.websocket_connect_ms),
        "websocket_reconnects={}".format(stats.websocket_reconnects),
        "websocket_reconnect_failures={}".format(stats.websocket_reconnect_failures),
        "consecutive_send_failures={}".format(stats.consecutive_send_failures),
        "samples_completed={}".format(stats.samples_completed),
        "servo_moves={}".format(stats.servo_moves),
        "sweep_passes={}".format(stats.sweep_passes),
        "sweep_cycles={}".format(stats.sweep_cycles),
        "servo_deg={:.1f}".format(stats.servo_deg),
        "ram_free_start={}".format(stats.ram_free_start),
        "ram_free_end={}".format(gc.mem_free()),
    ])
    emit("telemetry", event, "|".join(parts))


def drain_uart():
    while uart.any():
        pending = uart.any()
        if pending > UART_DRAIN_CHUNK_SIZE:
            pending = UART_DRAIN_CHUNK_SIZE
        uart.read(pending)


def find_header():
    while True:
        byte = uart.read(1)
        if byte:
            stats.bytes_received += 1
            if byte[0] == HEADER:
                return True
            stats.header_miss_count += 1


def connect_wifi():
    start_ms = time.ticks_ms()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected() and time.ticks_diff(time.ticks_ms(), start_ms) < 30000:
            time.sleep_ms(250)

    stats.wifi_connect_ms = time.ticks_diff(time.ticks_ms(), start_ms)
    stats.wifi_connected = 1 if wlan.isconnected() else 0
    return wlan if wlan.isconnected() else None


def websocket_handshake(sock):
    key = "dGhlIHNhbXBsZSBub25jZQ=="
    request = (
        "GET {} HTTP/1.1\r\n"
        "Host: {}:{}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: {}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    ).format(WEBSOCKET_PATH, SERVER_HOST, SERVER_PORT, key)
    sock.send(request.encode())
    response = sock.recv(512)
    if b"101" not in response.split(b"\r\n", 1)[0]:
        raise OSError("websocket handshake failed")


def connect_websocket():
    start_ms = time.ticks_ms()
    addr = socket.getaddrinfo(SERVER_HOST, SERVER_PORT)[0][-1]
    sock = socket.socket()
    sock.connect(addr)
    websocket_handshake(sock)
    sock.settimeout(SOCKET_SEND_TIMEOUT_S)
    stats.websocket_connect_ms = time.ticks_diff(time.ticks_ms(), start_ms)
    stats.websocket_connected = 1
    return sock


def reconnect_websocket(sock):
    if sock:
        try:
            sock.close()
        except Exception:
            pass

    for attempt in range(1, WS_RECONNECT_RETRIES + 1):
        try:
            new_sock = connect_websocket()
            stats.websocket_reconnects += 1
            emit("network", "ws_reconnected", "attempt={}".format(attempt))
            return new_sock
        except Exception:
            stats.websocket_reconnect_failures += 1
            time.sleep_ms(WS_RECONNECT_BACKOFF_MS)

    emit("network", "ws_reconnect_failed", "retries={}".format(WS_RECONNECT_RETRIES))
    return None


def send_websocket_message(sock, payload):
    payload_len = len(payload)
    mask = bytearray([urandom.getrandbits(8) for _ in range(4)])
    frame = bytearray()
    frame.append(0x81)

    if payload_len <= 125:
        frame.append(payload_len | 0x80)
    elif payload_len <= 65535:
        frame.append(126 | 0x80)
        frame.extend(struct.pack(">H", payload_len))
    else:
        frame.append(127 | 0x80)
        frame.extend(struct.pack(">Q", payload_len))

    frame.extend(mask)
    for i in range(payload_len):
        frame.append(payload[i] ^ mask[i % 4])

    send_start_us = time.ticks_us()
    sock.send(frame)
    stats.total_send_time_us += time.ticks_diff(time.ticks_us(), send_start_us)
    stats.messages_sent += 1
    stats.payload_bytes_sent += payload_len
    stats.websocket_frame_bytes_sent += len(frame)


def main():
    gc.collect()
    stats.ram_free_start = gc.mem_free()
    servo = ServoSweep(SERVO_PIN)
    servo.init()
    stats.servo_deg = servo.angle()
    emit(
        "telemetry",
        "session_start",
        "schema=1|firmware=micropython_ld19_network|target_duration_s=60|network_enabled=1|servo_enabled=1|server_host={}|server_port={}|servo_pin={}".format(SERVER_HOST, SERVER_PORT, SERVO_PIN),
    )

    wlan = connect_wifi()
    if not wlan:
        emit_stats("summary", "wifi_failed")
        emit("telemetry", "done", "reason=wifi_failed")
        return

    sock = None
    try:
        sock = connect_websocket()
        drain_uart()
        gc.collect()
        stats.start_ms = time.ticks_ms()
        stats.last_periodic_ms = stats.start_ms

        while time.ticks_diff(time.ticks_ms(), stats.start_ms) < NETWORK_DURATION_MS:
            frame_start_us = time.ticks_us()
            stats.servo_deg = servo.angle()

            if not find_header():
                continue

            remaining = uart.read(FRAME_SIZE - 1)
            if not remaining or len(remaining) != FRAME_SIZE - 1:
                stats.frames_size_error += 1
                continue

            frame = bytes([HEADER]) + remaining
            stats.bytes_received += len(remaining)
            stats.bytes_processed += FRAME_SIZE
            stats.frames_received += 1

            points = parse_lidar_points(frame)
            if points:
                frame_servo_deg = stats.servo_deg
                stats.frames_valid += 1
                stats.points_total += len(points)
                for point in points:
                    if servo.update_rotation(point["a"]):
                        stats.samples_completed += 1
                if servo.should_move():
                    servo.move_next()
                    stats.servo_moves += 1
                    stats.sweep_passes = servo.sweep_passes
                    stats.sweep_cycles = servo.sweep_cycles
                    stats.servo_deg = servo.angle()

                payload = ujson.dumps({"inclination": round(frame_servo_deg, 1), "points": points}).encode()
                try:
                    if sock is None:
                        sock = reconnect_websocket(sock)
                        if sock is None:
                            raise OSError("websocket unavailable")

                    send_websocket_message(sock, payload)
                    stats.consecutive_send_failures = 0
                except Exception:
                    stats.send_failures += 1
                    stats.consecutive_send_failures += 1
                    if stats.consecutive_send_failures >= WS_RECONNECT_TRIGGER_FAILS:
                        sock = reconnect_websocket(sock)
                        if sock:
                            stats.consecutive_send_failures = 0

                frame_time_us = time.ticks_diff(time.ticks_us(), frame_start_us)
                stats.total_frame_time_us += frame_time_us
                if stats.frames_valid == 1 or frame_time_us < stats.min_frame_time_us:
                    stats.min_frame_time_us = frame_time_us
                if frame_time_us > stats.max_frame_time_us:
                    stats.max_frame_time_us = frame_time_us

            now_ms = time.ticks_ms()
            if time.ticks_diff(now_ms, stats.last_periodic_ms) >= 1000:
                stats.last_periodic_ms = now_ms
                emit_stats("stats")

        gc.collect()
        emit_stats("summary", "duration_reached")
        emit("telemetry", "done", "reason=duration_reached")

    except Exception:
        emit_stats("summary", "network_error")
        emit("telemetry", "done", "reason=network_error")
    finally:
        if sock:
            sock.close()


if __name__ == "__main__":
    main()
