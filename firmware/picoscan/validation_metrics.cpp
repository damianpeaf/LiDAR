#include "validation_metrics.hpp"

#include <stdio.h>
#include <string.h>

#include "pico/time.h"

namespace
{
constexpr uint32_t SNAPSHOT_INTERVAL_MS = 5000;

struct ValidationState
{
    bool initialized;
    absolute_time_t next_snapshot_at;

    uint32_t uart_rx_overflow_count;
    uint16_t uart_ring_backlog_current;
    uint16_t uart_ring_backlog_max;

    uint32_t lidar_frames_valid;
    uint32_t lidar_frames_invalid;
    uint32_t lidar_parser_resync_count;
    uint32_t lidar_parse_failures;

    uint32_t points_enqueued;
    uint32_t points_dropped;
    uint16_t queue_backlog_current;
    uint16_t queue_backlog_max;

    uint32_t batches_sent;
    uint32_t points_sent;
    uint32_t packet_build_failures;
    uint32_t tcp_write_failures;
    int last_tcp_write_error;

    uint32_t servo_settling_entries;
    uint32_t servo_sampling_resumes;
    uint32_t servo_samples_completed;

    uint32_t connection_state_transitions;
    uint32_t handshake_successes;
    uint32_t handshake_failures;
    char connection_state[32];
};

ValidationState g_state = {};

uint32_t uptime_ms()
{
    return to_ms_since_boot(get_absolute_time());
}

void emit_event(const char *event_name, const char *details)
{
    printf(
        "VALIDATION_STATS {\"type\":\"event\",\"uptime_ms\":%u,\"event\":\"%s\"%s}\n",
        uptime_ms(),
        event_name,
        details != nullptr ? details : "");
}

void emit_snapshot(const char *reason)
{
    printf(
        "VALIDATION_STATS {\"type\":\"snapshot\",\"reason\":\"%s\",\"uptime_ms\":%u,\"connection_state\":\"%s\",\"uart\":{\"rx_overflow\":%lu,\"ring_backlog_current\":%u,\"ring_backlog_max\":%u},\"lidar\":{\"frames_valid\":%lu,\"frames_invalid\":%lu,\"parser_resync\":%lu,\"parse_failures\":%lu},\"points\":{\"enqueued\":%lu,\"dropped\":%lu,\"queue_backlog_current\":%u,\"queue_backlog_max\":%u},\"network\":{\"batches_sent\":%lu,\"points_sent\":%lu,\"packet_build_failures\":%lu,\"tcp_write_failures\":%lu,\"last_tcp_write_error\":%d,\"handshake_successes\":%lu,\"handshake_failures\":%lu},\"servo\":{\"enter_settling\":%lu,\"resume_sampling\":%lu,\"sample_complete\":%lu}}\n",
        reason,
        uptime_ms(),
        g_state.connection_state,
        static_cast<unsigned long>(g_state.uart_rx_overflow_count),
        g_state.uart_ring_backlog_current,
        g_state.uart_ring_backlog_max,
        static_cast<unsigned long>(g_state.lidar_frames_valid),
        static_cast<unsigned long>(g_state.lidar_frames_invalid),
        static_cast<unsigned long>(g_state.lidar_parser_resync_count),
        static_cast<unsigned long>(g_state.lidar_parse_failures),
        static_cast<unsigned long>(g_state.points_enqueued),
        static_cast<unsigned long>(g_state.points_dropped),
        g_state.queue_backlog_current,
        g_state.queue_backlog_max,
        static_cast<unsigned long>(g_state.batches_sent),
        static_cast<unsigned long>(g_state.points_sent),
        static_cast<unsigned long>(g_state.packet_build_failures),
        static_cast<unsigned long>(g_state.tcp_write_failures),
        g_state.last_tcp_write_error,
        static_cast<unsigned long>(g_state.handshake_successes),
        static_cast<unsigned long>(g_state.handshake_failures),
        static_cast<unsigned long>(g_state.servo_settling_entries),
        static_cast<unsigned long>(g_state.servo_sampling_resumes),
        static_cast<unsigned long>(g_state.servo_samples_completed));
}

void set_connection_state_internal(const char *state_name, bool emit_transition)
{
    if (state_name == nullptr)
    {
        return;
    }

    if (strncmp(g_state.connection_state, state_name, sizeof(g_state.connection_state)) == 0)
    {
        return;
    }

    snprintf(g_state.connection_state, sizeof(g_state.connection_state), "%s", state_name);
    g_state.connection_state_transitions++;

    if (emit_transition)
    {
        char details[96];
        snprintf(details, sizeof(details), ",\"connection_state\":\"%s\"", g_state.connection_state);
        emit_event("connection_state", details);
    }
}
} // namespace

namespace ValidationMetrics
{
void init()
{
    memset(&g_state, 0, sizeof(g_state));
    g_state.initialized = true;
    g_state.last_tcp_write_error = 0;
    set_connection_state_internal("boot", false);
    g_state.next_snapshot_at = make_timeout_time_ms(SNAPSHOT_INTERVAL_MS);
    emit_event("validation_init", "");
}

void tick()
{
    if (!g_state.initialized)
    {
        return;
    }

    if (time_reached(g_state.next_snapshot_at))
    {
        emit_snapshot("periodic");
        g_state.next_snapshot_at = make_timeout_time_ms(SNAPSHOT_INTERVAL_MS);
    }
}

void note_uart_ring_snapshot(uint32_t overflow_count, uint16_t current_backlog, uint16_t max_backlog)
{
    g_state.uart_rx_overflow_count = overflow_count;
    g_state.uart_ring_backlog_current = current_backlog;
    if (max_backlog > g_state.uart_ring_backlog_max)
    {
        g_state.uart_ring_backlog_max = max_backlog;
    }
}

void note_lidar_frame_valid() { g_state.lidar_frames_valid++; }
void note_lidar_frame_invalid() { g_state.lidar_frames_invalid++; }
void note_lidar_parser_resync() { g_state.lidar_parser_resync_count++; }
void note_lidar_parse_failure() { g_state.lidar_parse_failures++; }

void note_point_enqueued() { g_state.points_enqueued++; }
void note_point_dropped() { g_state.points_dropped++; }

void note_queue_backlog(uint16_t backlog)
{
    g_state.queue_backlog_current = backlog;
    if (backlog > g_state.queue_backlog_max)
    {
        g_state.queue_backlog_max = backlog;
    }
}

void note_batch_sent(uint16_t points_sent, uint16_t backlog_after_send)
{
    g_state.batches_sent++;
    g_state.points_sent += points_sent;
    note_queue_backlog(backlog_after_send);
}

void note_packet_build_failure() { g_state.packet_build_failures++; }

void note_tcp_write_failure(int error_code)
{
    g_state.tcp_write_failures++;
    g_state.last_tcp_write_error = error_code;
}

void note_servo_enter_settling(float servo_angle_deg)
{
    g_state.servo_settling_entries++;
    char details[128];
    snprintf(details, sizeof(details), ",\"servo_angle_deg\":%.1f", servo_angle_deg);
    emit_event("servo_enter_settling", details);
}

void note_servo_resume_sampling(float servo_angle_deg)
{
    g_state.servo_sampling_resumes++;
    char details[128];
    snprintf(details, sizeof(details), ",\"servo_angle_deg\":%.1f", servo_angle_deg);
    emit_event("servo_resume_sampling", details);
}

void note_servo_sample_complete(float servo_angle_deg, int sample_number, int points_in_sample)
{
    g_state.servo_samples_completed++;
    char details[160];
    snprintf(details,
             sizeof(details),
             ",\"servo_angle_deg\":%.1f,\"sample_number\":%d,\"points_in_sample\":%d",
             servo_angle_deg,
             sample_number,
             points_in_sample);
    emit_event("servo_sample_complete", details);
}

void note_connection_state(const char *state_name)
{
    set_connection_state_internal(state_name, true);
}

void note_handshake_result(bool success)
{
    if (success)
    {
        g_state.handshake_successes++;
        emit_event("handshake_completed", "");
    }
    else
    {
        g_state.handshake_failures++;
        emit_event("handshake_failed", "");
    }
}
} // namespace ValidationMetrics
