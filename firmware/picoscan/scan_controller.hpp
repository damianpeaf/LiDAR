#pragma once

#include "hardware/uart.h"
#include "servo_controller.hpp"
#include "tcp_client.hpp"
#include "lidar.hpp"

struct ScanParams {
    int batch_size = 100;
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
};
