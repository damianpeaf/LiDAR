#include <cstdio>
#include <cmath>
#include "pico/time.h"
#include "scan_controller.hpp"
#include "telemetry.hpp"
#include "uart_utils.hpp"

ScanController::ScanController(ServoController& servo, TCPClient& tcp, uart_inst_t* uart)
    : servo_(servo), tcp_(tcp), uart_(uart), state_(State::STOPPED), dropped_points_(0)
{
}

void ScanController::start()
{
    if (state_ == State::STOPPED) {
        parser_.reset();
        state_ = State::RUNNING;
        printf("[scan] started\n");
        telemetry::note_scan_started();
    }
}

void ScanController::stop()
{
    state_ = State::STOPPED;
    printf("[scan] stopped\n");
    telemetry::note_scan_stopped("manual");
}

void ScanController::pause()
{
    if (state_ == State::RUNNING) {
        state_ = State::PAUSED;
        printf("[scan] paused\n");
    }
}

void ScanController::resume()
{
    if (state_ == State::PAUSED) {
        state_ = State::RUNNING;
        printf("[scan] resumed\n");
    }
}

void ScanController::set_params(const ScanParams& params)
{
    params_ = params;
}

bool ScanController::network_enabled() const { return params_.enable_network; }

bool ScanController::is_running() const { return state_ == State::RUNNING; }
bool ScanController::is_paused()  const { return state_ == State::PAUSED;  }
bool ScanController::is_stopped() const { return state_ == State::STOPPED; }

bool ScanController::should_emit_point(float angle) const
{
    if (!params_.emit_point_events) {
        return false;
    }

    if (!params_.filter_point_events_by_angle) {
        return telemetry::should_emit_point_event();
    }

    float diff = fabsf(fmodf(angle - params_.point_event_angle_center_deg + 540.0f, 360.0f) - 180.0f);
    if (diff > params_.point_event_angle_half_width_deg) {
        return false;
    }

    return telemetry::should_emit_point_event();
}

void ScanController::update()
{
    if (params_.enable_servo) {
        servo_.update();
    }

    if (state_ != State::RUNNING)
        return;

    process_lidar_frame();
    handle_transmission();
}

void ScanController::process_lidar_frame()
{
    uint8_t frame[FRAME_SIZE];
    LidarPoint points[POINT_PER_PACK];

    uint8_t byte;
    uint64_t frame_read_time_us = 0;
    while (true) {
        const uint64_t uart_poll_start_us = time_us_64();
        if (!uart_read_byte_timeout(uart_, &byte, 0)) {
            telemetry::note_uart_poll_time(time_us_64() - uart_poll_start_us);
            break;
        }

        telemetry::note_uart_poll_time(time_us_64() - uart_poll_start_us);
        telemetry::note_uart_byte();

        if (parser_.push_byte(byte, frame, &frame_read_time_us)) {
            const uint64_t parse_start_us = time_us_64();
            int num_points = parse_points(frame, points);
            const uint64_t parse_time_us = time_us_64() - parse_start_us;
            float servo_angle = servo_.get_current_angle();

            telemetry::note_frame_valid(num_points, frame_read_time_us + parse_time_us, parse_time_us, servo_angle);

            for (int i = 0; i < num_points; i++) {
                if (points[i].distance <= 0 || points[i].distance > 12000 ||
                    points[i].angle < 0 || points[i].angle > 360)
                    continue;

                if (should_emit_point(points[i].angle)) {
                    telemetry::note_point_event(points[i].angle, points[i].distance, points[i].intensity, servo_angle);
                }

                if (params_.enable_servo && servo_.check_complete_lidar_rotation(points[i].angle)) {
                    printf("[scan] sample complete at servo %.1f°\n", servo_angle);
                }

                if (!params_.enable_network) {
                    continue;
                }

                if (tcp_.is_point_queue_full()) {
                    dropped_points_++;
                    telemetry::note_point_dropped();
                    if (dropped_points_ % BACKPRESSURE_LOG_INTERVAL == 1)
                        printf("[scan] backpressure: %lu pts dropped\n",
                               (unsigned long)dropped_points_);
                    continue;
                }
                tcp_.add_point(points[i].angle, points[i].distance,
                               points[i].intensity, servo_angle);
                telemetry::note_queue_depth(tcp_.get_points_count());
            }

            if (params_.enable_servo && servo_.should_move_servo()) {
                printf("[scan] position complete, moving servo\n");
                servo_.move_to_next_position();
            }
        }
    }

    telemetry::maybe_emit_periodic(servo_.get_current_angle(), params_.enable_network ? tcp_.get_points_count() : 0, servo_.is_ready_for_sampling());

    if ((params_.target_duration_s > 0 && telemetry::duration_reached()) ||
        (params_.target_point_events > 0 && telemetry::point_target_reached())) {
        telemetry::emit_summary(params_.target_duration_s > 0 ? "duration_reached" : "point_target_reached",
                                servo_.get_current_angle(),
                                params_.enable_network ? tcp_.get_points_count() : 0);
        telemetry::emit("telemetry", "done", "reason=%s",
                        params_.target_duration_s > 0 ? "duration_reached" : "point_target_reached");
        telemetry::note_scan_stopped(params_.target_duration_s > 0 ? "duration_reached" : "point_target_reached");
        state_ = State::STOPPED;
    }
}

void ScanController::handle_transmission()
{
    if (!params_.enable_network) {
        return;
    }

    int count = tcp_.get_points_count();

    while (count >= params_.batch_size) {
        if (!tcp_.send_points_batch(params_.batch_size))
            break;

        count = tcp_.get_points_count();
    }
}
