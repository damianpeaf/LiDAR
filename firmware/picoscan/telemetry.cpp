#include "telemetry.hpp"

#include <cstdarg>
#include <cstdio>
#include <cstring>

#include "pico/time.h"

namespace {

struct TelemetryStats {
    TelemetryOptions options;
    uint64_t session_start_us = 0;
    uint64_t last_periodic_us = 0;
    uint64_t raw_bytes_received = 0;
    uint64_t frame_candidate_count = 0;
    uint64_t frame_valid_count = 0;
    uint64_t frame_crc_error_count = 0;
    uint64_t header_miss_count = 0;
    uint64_t parser_resync_count = 0;
    uint64_t bytes_processed = 0;
    uint64_t points_valid_total = 0;
    uint64_t points_dropped_total = 0;
    uint64_t point_events_emitted = 0;
    uint64_t point_stride_counter = 0;
    uint64_t sample_complete_count = 0;
    uint64_t servo_move_count = 0;
    uint64_t sweep_pass_count = 0;
    uint64_t sweep_cycle_count = 0;
    uint64_t batches_sent = 0;
    uint64_t batch_send_failures = 0;
    uint64_t payload_bytes_sent = 0;
    uint64_t websocket_frame_bytes_sent = 0;
    uint64_t uart_poll_time_us = 0;
    uint64_t total_frame_time_us = 0;
    uint64_t total_parse_time_us = 0;
    uint64_t min_frame_time_us = 0;
    uint64_t max_frame_time_us = 0;
    int max_queue_depth = 0;
    bool initialized = false;
};

TelemetryStats stats;

float safe_divide(float numerator, float denominator)
{
    if (denominator <= 0.0f) {
        return 0.0f;
    }
    return numerator / denominator;
}

void emitv(const char *component, const char *event, const char *extra_fmt, va_list args)
{
    char extra[1024] = {0};
    if (extra_fmt != nullptr && extra_fmt[0] != '\0') {
        vsnprintf(extra, sizeof(extra), extra_fmt, args);
    }

    printf("EXP|ts_us=%llu|profile=%s|component=%s|event=%s",
           time_us_64(),
           telemetry::profile_name(stats.options.profile),
           component,
           event);

    if (extra[0] != '\0') {
        printf("|%s", extra);
    }

    printf("\n");
}

} // namespace

namespace telemetry {

void init(const TelemetryOptions &options)
{
    memset(&stats, 0, sizeof(stats));
    stats.options = options;
    stats.session_start_us = time_us_64();
    stats.last_periodic_us = stats.session_start_us;
    stats.initialized = true;

    emit("telemetry", "session_start",
         "schema=1|firmware=picoscan|periodic_interval_ms=%lu|target_duration_s=%lu|target_point_events=%lu|point_stride=%lu|servo_enabled=%d|network_enabled=%d",
         static_cast<unsigned long>(options.periodic_interval_ms),
         static_cast<unsigned long>(options.target_duration_s),
         static_cast<unsigned long>(options.target_point_events),
         static_cast<unsigned long>(options.point_stride),
         options.servo_enabled ? 1 : 0,
         options.network_enabled ? 1 : 0);
}

const TelemetryOptions &options()
{
    return stats.options;
}

const char *profile_name(ExperimentProfile profile)
{
    switch (profile) {
        case ExperimentProfile::Scan:
            return "scan";
        case ExperimentProfile::Benchmark:
            return "benchmark";
        case ExperimentProfile::Precision:
            return "precision";
        default:
            return "unknown";
    }
}

void emit(const char *component, const char *event, const char *extra_fmt, ...)
{
    va_list args;
    va_start(args, extra_fmt);
    emitv(component, event, extra_fmt, args);
    va_end(args);
}

void note_boot(bool forced_setup, bool has_config)
{
    emit("app", "boot", "forced_setup=%d|has_config=%d", forced_setup ? 1 : 0, has_config ? 1 : 0);
}

void note_config_loaded(const char *ssid, const char *tcp_ip, uint16_t tcp_port, uint16_t batch_size)
{
    emit("config", "loaded", "wifi_ssid=%s|tcp_ip=%s|tcp_port=%u|batch_size=%u",
         ssid,
         tcp_ip,
         tcp_port,
         batch_size);
}

void note_state_transition(const char *from, const char *to)
{
    emit("device", "state_transition", "from=%s|to=%s", from, to);
}

void note_scan_started()
{
    emit("scan", "started");
}

void note_scan_stopped(const char *reason)
{
    emit("scan", "stopped", "reason=%s", reason);
}

void note_wifi_event(const char *event, const char *detail)
{
    if (detail != nullptr && detail[0] != '\0') {
        emit("wifi", event, "detail=%s", detail);
        return;
    }
    emit("wifi", event);
}

void note_tcp_event(const char *event, int code, int queue_depth)
{
    emit("tcp", event, "code=%d|queue_depth=%d", code, queue_depth);
}

void note_uart_byte()
{
    stats.raw_bytes_received++;
}

void note_uart_poll_time(uint64_t elapsed_us)
{
    stats.uart_poll_time_us += elapsed_us;
}

void note_header_miss()
{
    stats.header_miss_count++;
}

void note_frame_candidate()
{
    stats.frame_candidate_count++;
    stats.bytes_processed += 47;
}

void note_frame_valid(uint32_t valid_points, uint64_t frame_time_us, uint64_t parse_time_us, float servo_angle)
{
    stats.frame_valid_count++;
    stats.points_valid_total += valid_points;
    stats.total_frame_time_us += frame_time_us;
    stats.total_parse_time_us += parse_time_us;

    if (stats.frame_valid_count == 1 || frame_time_us < stats.min_frame_time_us) {
        stats.min_frame_time_us = frame_time_us;
    }
    if (frame_time_us > stats.max_frame_time_us) {
        stats.max_frame_time_us = frame_time_us;
    }

    (void)servo_angle;
}

void note_frame_crc_error(uint64_t frame_time_us)
{
    stats.frame_crc_error_count++;
    stats.total_frame_time_us += frame_time_us;

    if ((stats.frame_valid_count + stats.frame_crc_error_count) == 1 || frame_time_us < stats.min_frame_time_us) {
        stats.min_frame_time_us = frame_time_us;
    }
    if (frame_time_us > stats.max_frame_time_us) {
        stats.max_frame_time_us = frame_time_us;
    }
}

void note_parser_resync(size_t retained_bytes)
{
    stats.parser_resync_count++;
    emit("lidar", "parser_resync", "retained_bytes=%u", static_cast<unsigned>(retained_bytes));
}

bool should_emit_point_event()
{
    if (stats.options.point_stride == 0) {
        return false;
    }

    stats.point_stride_counter++;
    return (stats.point_stride_counter % stats.options.point_stride) == 0;
}

void note_point_event(float pan_angle, uint16_t distance_mm, uint8_t intensity, float servo_angle)
{
    stats.point_events_emitted++;
    emit("measurement", "point", "index=%llu|pan_deg=%.1f|distance_mm=%u|intensity=%u|servo_deg=%.1f",
         stats.point_events_emitted,
         pan_angle,
         distance_mm,
         intensity,
         servo_angle);
}

bool point_target_reached()
{
    return stats.options.target_point_events > 0 && stats.point_events_emitted >= stats.options.target_point_events;
}

void note_point_dropped()
{
    stats.points_dropped_total++;
}

void note_queue_depth(int depth)
{
    if (depth > stats.max_queue_depth) {
        stats.max_queue_depth = depth;
    }
}

void note_batch_sent(int points_in_payload, int payload_bytes, int websocket_frame_bytes, int queue_remaining, float servo_angle)
{
    stats.batches_sent++;
    stats.payload_bytes_sent += payload_bytes;
    stats.websocket_frame_bytes_sent += websocket_frame_bytes;
    note_queue_depth(queue_remaining);
    emit("tcp", "batch_sent", "points=%d|payload_bytes=%d|websocket_frame_bytes=%d|queue_remaining=%d|servo_deg=%.1f",
         points_in_payload,
         payload_bytes,
         websocket_frame_bytes,
         queue_remaining,
         servo_angle);
}

void note_batch_send_failed(const char *reason, int queue_depth)
{
    stats.batch_send_failures++;
    emit("tcp", "batch_failed", "reason=%s|queue_depth=%d", reason, queue_depth);
}

void note_sample_complete(float servo_angle, int sample_index, int points_in_sample)
{
    stats.sample_complete_count++;
    emit("scan", "sample_complete", "sample_index=%d|servo_deg=%.1f|points=%d",
         sample_index,
         servo_angle,
         points_in_sample);
}

void note_servo_move(float from_angle, float to_angle, const char *endpoint, int direction)
{
    stats.servo_move_count++;
    emit("servo", "move", "from_deg=%.1f|to_deg=%.1f|direction=%d|endpoint=%s",
         from_angle,
         to_angle,
         direction,
         endpoint);
}

void note_servo_settled(float angle)
{
    emit("servo", "settled", "angle_deg=%.1f", angle);
}

void note_scan_cycle_event(const char *event, float servo_angle, uint32_t sweep_passes, uint32_t sweep_cycles)
{
    stats.sweep_pass_count = sweep_passes;
    stats.sweep_cycle_count = sweep_cycles;
    emit("scan", event, "servo_deg=%.1f|sweep_passes=%lu|sweep_cycles=%lu",
         servo_angle,
         static_cast<unsigned long>(sweep_passes),
         static_cast<unsigned long>(sweep_cycles));
}

void maybe_emit_periodic(float servo_angle, int queue_depth, bool servo_ready)
{
    const uint64_t now_us = time_us_64();
    if (stats.options.periodic_interval_ms == 0) {
        return;
    }
    if (now_us - stats.last_periodic_us < static_cast<uint64_t>(stats.options.periodic_interval_ms) * 1000ULL) {
        return;
    }

    stats.last_periodic_us = now_us;

    const float elapsed_s = safe_divide(static_cast<float>(now_us - stats.session_start_us), 1000000.0f);
    const float frames_per_s = safe_divide(static_cast<float>(stats.frame_valid_count), elapsed_s);
    const float points_per_s = safe_divide(static_cast<float>(stats.points_valid_total), elapsed_s);
    const float bytes_per_s = safe_divide(static_cast<float>(stats.raw_bytes_received), elapsed_s);
    const float payload_bytes_per_s = safe_divide(static_cast<float>(stats.payload_bytes_sent), elapsed_s);
    const float websocket_frame_bytes_per_s = safe_divide(static_cast<float>(stats.websocket_frame_bytes_sent), elapsed_s);
    const uint64_t avg_frame_time = (stats.frame_valid_count > 0)
        ? stats.total_frame_time_us / stats.frame_valid_count
        : 0;
    const uint64_t avg_parse_time = (stats.frame_valid_count > 0)
        ? stats.total_parse_time_us / stats.frame_valid_count
        : 0;
    const uint64_t avg_uart_poll_time = (stats.frame_candidate_count > 0)
        ? stats.uart_poll_time_us / stats.frame_candidate_count
        : 0;

    emit("telemetry", "stats",
         "elapsed_s=%.3f|bytes_received=%llu|bytes_processed=%llu|frames_received=%llu|frames_valid=%llu|frames_crc_error=%llu|frames_header_error=%llu|parser_resyncs=%llu|points_total=%llu|points_dropped=%llu|frames_per_s=%.3f|points_per_s=%.3f|bytes_per_s=%.3f|payload_bytes_sent=%llu|payload_bytes_per_s=%.3f|websocket_frame_bytes_sent=%llu|websocket_frame_bytes_per_s=%.3f|batch_failures=%llu|avg_frame_time_us=%llu|avg_parse_time_us=%llu|avg_uart_poll_time_us=%llu|max_queue_depth=%d|queue_depth=%d|servo_deg=%.1f|servo_ready=%d|sample_count=%llu|sweep_passes=%llu|sweep_cycles=%llu",
         elapsed_s,
         stats.raw_bytes_received,
         stats.bytes_processed,
         stats.frame_candidate_count,
         stats.frame_valid_count,
         stats.frame_crc_error_count,
         stats.header_miss_count,
         stats.parser_resync_count,
         stats.points_valid_total,
         stats.points_dropped_total,
         frames_per_s,
         points_per_s,
         bytes_per_s,
         stats.payload_bytes_sent,
         payload_bytes_per_s,
         stats.websocket_frame_bytes_sent,
         websocket_frame_bytes_per_s,
         stats.batch_send_failures,
         avg_frame_time,
         avg_parse_time,
         avg_uart_poll_time,
         stats.max_queue_depth,
         queue_depth,
         servo_angle,
         servo_ready ? 1 : 0,
         stats.sample_complete_count,
         stats.sweep_pass_count,
         stats.sweep_cycle_count);
}

void emit_summary(const char *reason, float servo_angle, int queue_depth)
{
    const uint64_t now_us = time_us_64();
    const float elapsed_s = safe_divide(static_cast<float>(now_us - stats.session_start_us), 1000000.0f);
    const float frames_per_s = safe_divide(static_cast<float>(stats.frame_valid_count), elapsed_s);
    const float points_per_s = safe_divide(static_cast<float>(stats.points_valid_total), elapsed_s);
    const float bytes_per_s = safe_divide(static_cast<float>(stats.raw_bytes_received), elapsed_s);
    const float payload_bytes_per_s = safe_divide(static_cast<float>(stats.payload_bytes_sent), elapsed_s);
    const float websocket_frame_bytes_per_s = safe_divide(static_cast<float>(stats.websocket_frame_bytes_sent), elapsed_s);
    const float avg_payload_bytes_per_batch = safe_divide(static_cast<float>(stats.payload_bytes_sent), static_cast<float>(stats.batches_sent));
    const float avg_websocket_frame_bytes_per_batch = safe_divide(static_cast<float>(stats.websocket_frame_bytes_sent), static_cast<float>(stats.batches_sent));
    const float success_rate = safe_divide(static_cast<float>(stats.frame_valid_count) * 100.0f,
                                           static_cast<float>(stats.frame_candidate_count));
    const float error_rate = safe_divide(static_cast<float>(stats.frame_crc_error_count + stats.header_miss_count) * 100.0f,
                                         static_cast<float>(stats.frame_candidate_count));
    const uint64_t avg_frame_time = (stats.frame_valid_count > 0)
        ? stats.total_frame_time_us / stats.frame_valid_count
        : 0;
    const uint64_t avg_parse_time = (stats.frame_valid_count > 0)
        ? stats.total_parse_time_us / stats.frame_valid_count
        : 0;
    const uint64_t avg_uart_poll_time = (stats.frame_candidate_count > 0)
        ? stats.uart_poll_time_us / stats.frame_candidate_count
        : 0;

    emit("telemetry", "summary",
         "reason=%s|duration_s=%.3f|bytes_received=%llu|bytes_processed=%llu|frames_received=%llu|frames_valid=%llu|frames_crc_error=%llu|frames_header_error=%llu|parser_resyncs=%llu|points_total=%llu|point_events=%llu|points_dropped=%llu|frames_per_s=%.3f|points_per_s=%.3f|bytes_per_s=%.3f|payload_bytes_sent=%llu|payload_bytes_per_s=%.3f|websocket_frame_bytes_sent=%llu|websocket_frame_bytes_per_s=%.3f|avg_payload_bytes_per_batch=%.3f|avg_websocket_frame_bytes_per_batch=%.3f|avg_frame_time_us=%llu|min_frame_time_us=%llu|max_frame_time_us=%llu|avg_parse_time_us=%llu|avg_uart_poll_time_us=%llu|success_rate_pct=%.3f|error_rate_pct=%.3f|samples_completed=%llu|servo_moves=%llu|sweep_passes=%llu|sweep_cycles=%llu|batches_sent=%llu|batch_failures=%llu|max_queue_depth=%d|queue_depth=%d|servo_deg=%.1f",
         reason,
         elapsed_s,
         stats.raw_bytes_received,
         stats.bytes_processed,
         stats.frame_candidate_count,
         stats.frame_valid_count,
         stats.frame_crc_error_count,
         stats.header_miss_count,
         stats.parser_resync_count,
         stats.points_valid_total,
         stats.point_events_emitted,
         stats.points_dropped_total,
         frames_per_s,
         points_per_s,
         bytes_per_s,
         stats.payload_bytes_sent,
         payload_bytes_per_s,
         stats.websocket_frame_bytes_sent,
         websocket_frame_bytes_per_s,
         avg_payload_bytes_per_batch,
         avg_websocket_frame_bytes_per_batch,
         avg_frame_time,
         stats.min_frame_time_us,
         stats.max_frame_time_us,
         avg_parse_time,
         avg_uart_poll_time,
         success_rate,
         error_rate,
         stats.sample_complete_count,
         stats.servo_move_count,
         stats.sweep_pass_count,
         stats.sweep_cycle_count,
         stats.batches_sent,
         stats.batch_send_failures,
         stats.max_queue_depth,
         queue_depth,
         servo_angle);
}

bool duration_reached()
{
    if (stats.options.target_duration_s == 0) {
        return false;
    }

    return (time_us_64() - stats.session_start_us) >= static_cast<uint64_t>(stats.options.target_duration_s) * 1000000ULL;
}

} // namespace telemetry
