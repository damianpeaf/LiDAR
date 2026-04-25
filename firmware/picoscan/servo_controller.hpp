#ifndef SERVO_CONTROLLER_HPP
#define SERVO_CONTROLLER_HPP

#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/pwm.h"

class ServoController
{
private:
    enum class State
    {
        Sampling,
        Settling,
    };

    uint gpio_pin;
    uint slice_num;
    uint16_t wrap_value;
    uint current_pulse;
    uint min_pulse;
    uint max_pulse;
    int direction;
    int samples_collected;
    int points_in_sample;
    uint32_t sweep_passes;
    uint32_t sweep_cycles;
    float last_lidar_angle;
    bool waiting_for_rotation;
    State state;
    absolute_time_t settle_deadline;

    static constexpr uint SERVO_MIN_PULSE = 500;
    static constexpr uint SERVO_MAX_PULSE = 2500;
    static constexpr uint SERVO_STEP_SIZE = 5;
    static constexpr int SAMPLES_PER_POSITION = 5;
    static constexpr int MIN_POINTS_PER_SAMPLE = 500;
    static constexpr uint32_t SERVO_SETTLE_MS = 400;

public:
    ServoController(uint pin);

    void configure_sweep(float min_angle_deg, float max_angle_deg);
    void init();
    void update();
    float pulse_to_degrees(uint pulse_us) const;
    void set_pulse_us(uint pulse_us);
    void move_to_next_position();
    bool check_complete_lidar_rotation(float current_angle);
    bool should_move_servo() const;
    float get_current_angle() const;
    uint32_t get_sweep_passes() const;
    bool is_ready_for_sampling() const;
    void reset_sampling_state();
};

#endif // SERVO_CONTROLLER_HPP
