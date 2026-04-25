#pragma once

#include "hardware/uart.h"
#include "servo_controller.hpp"
#include "tcp_client.hpp"
#include "lidar.hpp"

struct ScanParams {
    int batch_size = 100;
    bool enable_servo = true;
    bool enable_network = true;
    bool emit_point_events = false;
    bool filter_point_events_by_angle = false;
    bool discard_points_outside_angle_window = false;
    float point_event_angle_center_deg = 0.0f;
    float point_event_angle_half_width_deg = 0.0f;
    uint32_t target_duration_s = 0;
    uint32_t target_point_events = 0;
    uint32_t target_sweep_passes = 0;
};

class ScanController {
public:
    ScanController(ServoController& servo, TCPClient& tcp, uart_inst_t* uart);

    void start();
    void stop();
    void pause();
    void resume();

    void update();

    bool is_running() const;
    bool is_paused() const;
    bool is_stopped() const;

    void set_params(const ScanParams& params);
    bool network_enabled() const;

private:
    static constexpr int BACKPRESSURE_LOG_INTERVAL = 500;

    enum class State { STOPPED, RUNNING, PAUSED };

    ServoController& servo_;
    TCPClient& tcp_;
    uart_inst_t* uart_;
    ScanParams params_;
    State state_;
    LidarFrameParser parser_;
    uint32_t dropped_points_;

    void process_lidar_frame();
    void handle_transmission();
    bool is_angle_inside_window(float angle) const;
    bool should_emit_point(float angle) const;
};
