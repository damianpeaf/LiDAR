#ifndef VALIDATION_METRICS_HPP
#define VALIDATION_METRICS_HPP

#include <stdint.h>

namespace ValidationMetrics
{
void init();
void tick();

void note_uart_ring_snapshot(uint32_t overflow_count, uint16_t current_backlog, uint16_t max_backlog);

void note_lidar_frame_valid();
void note_lidar_frame_invalid();
void note_lidar_parser_resync();
void note_lidar_parse_failure();

void note_point_enqueued();
void note_point_dropped();
void note_queue_backlog(uint16_t backlog);

void note_batch_sent(uint16_t points_sent, uint16_t backlog_after_send);
void note_packet_build_failure();
void note_tcp_write_failure(int error_code);

void note_servo_enter_settling(float servo_angle_deg);
void note_servo_resume_sampling(float servo_angle_deg);
void note_servo_sample_complete(float servo_angle_deg, int sample_number, int points_in_sample);

void note_connection_state(const char *state_name);
void note_handshake_result(bool success);
}

#endif // VALIDATION_METRICS_HPP
