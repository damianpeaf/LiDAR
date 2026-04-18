#include <cstdio>
#include "scan_controller.hpp"
#include "uart_utils.hpp"

ScanController::ScanController(ServoController& servo, TCPClient& tcp, uart_inst_t* uart)
    : servo_(servo), tcp_(tcp), uart_(uart), state_(State::STOPPED)
{
}

void ScanController::start()
{
    if (state_ == State::STOPPED) {
        parser_.reset();
        state_ = State::RUNNING;
        printf("[scan] started\n");
    }
}

void ScanController::stop()
{
    state_ = State::STOPPED;
    printf("[scan] stopped\n");
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

bool ScanController::is_running() const { return state_ == State::RUNNING; }
bool ScanController::is_paused()  const { return state_ == State::PAUSED;  }
bool ScanController::is_stopped() const { return state_ == State::STOPPED; }

void ScanController::update()
{
    servo_.update();

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
    while (uart_read_byte_timeout(uart_, &byte, 0)) {
        if (parser_.push_byte(byte, frame)) {
            int num_points = parse_points(frame, points);
            float servo_angle = servo_.get_current_angle();

            for (int i = 0; i < num_points; i++) {
                if (points[i].distance <= 0 || points[i].distance > 12000 ||
                    points[i].angle < 0 || points[i].angle > 360)
                    continue;

                if (servo_.check_complete_lidar_rotation(points[i].angle)) {
                    printf("[scan] sample complete at servo %.1f°\n", servo_angle);
                }

                tcp_.add_point(points[i].angle, points[i].distance,
                               points[i].intensity, servo_angle);
            }

            if (servo_.should_move_servo()) {
                printf("[scan] position complete, moving servo\n");
                servo_.move_to_next_position();
            }
        }
    }
}

void ScanController::handle_transmission()
{
    while (tcp_.get_points_count() >= params_.batch_size) {
        if (!tcp_.send_points_batch(params_.batch_size))
            break;
    }
}
