#pragma once

#include <cstddef>
#include <cstdint>

enum class ExperimentProfile : uint8_t {
    Scan = 0,
    Benchmark = 1,
    Precision = 2,
};

struct TelemetryOptions {
    ExperimentProfile profile = ExperimentProfile::Scan;
    uint32_t periodic_interval_ms = 1000;
    uint32_t target_duration_s = 0;
    uint32_t target_point_events = 0;
    uint32_t point_stride = 0;
    bool servo_enabled = true;
    bool network_enabled = true;
};

namespace telemetry {

void init(const TelemetryOptions &options);
const TelemetryOptions &options();
const char *profile_name(ExperimentProfile profile);

void emit(const char *component, const char *event, const char *extra_fmt = nullptr, ...);

void note_boot(bool forced_setup, bool has_config);
void note_config_loaded(const char *ssid, const char *tcp_ip, uint16_t tcp_port, uint16_t batch_size);
void note_state_transition(const char *from, const char *to);
void note_scan_started();
void note_scan_stopped(const char *reason);

void note_wifi_event(const char *event, const char *detail = nullptr);
void note_tcp_event(const char *event, int code = 0, int queue_depth = 0);

void note_uart_byte();
void note_uart_poll_time(uint64_t elapsed_us);
void note_header_miss();
void note_frame_candidate();
void note_frame_valid(uint32_t valid_points, uint64_t frame_time_us, uint64_t parse_time_us, float servo_angle);
void note_frame_crc_error(uint64_t frame_time_us);
void note_parser_resync(size_t retained_bytes);

void note_point_event(float pan_angle, uint16_t distance_mm, uint8_t intensity, float servo_angle);
bool should_emit_point_event();
bool point_target_reached();

void note_point_dropped();
void note_queue_depth(int depth);
void note_batch_sent(int points_in_payload, int payload_bytes, int queue_remaining, float servo_angle);
void note_batch_send_failed(const char *reason, int queue_depth);

void note_sample_complete(float servo_angle, int sample_index, int points_in_sample);
void note_servo_move(float from_angle, float to_angle, const char *endpoint, int direction);
void note_servo_settled(float angle);
void note_scan_cycle_event(const char *event, float servo_angle, uint32_t sweep_passes, uint32_t sweep_cycles);

void maybe_emit_periodic(float servo_angle, int queue_depth, bool servo_ready);
void emit_summary(const char *reason, float servo_angle, int queue_depth);
bool duration_reached();

}
