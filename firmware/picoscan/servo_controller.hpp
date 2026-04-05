#ifndef SERVO_CONTROLLER_HPP
#define SERVO_CONTROLLER_HPP

#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/pwm.h"

class ServoController
{
private:
    uint gpio_pin;
    uint slice_num;
    uint16_t wrap_value;
    uint current_pulse;
    int direction;
    int samples_collected;
    int points_in_sample;
    float last_lidar_angle;
    bool waiting_for_rotation;

    static constexpr uint SERVO_MIN_PULSE = 500;
    static constexpr uint SERVO_MAX_PULSE = 2500;
    static constexpr uint SERVO_STEP_SIZE = 10;
    static constexpr int SAMPLES_PER_POSITION = 3;
    static constexpr int MIN_POINTS_PER_SAMPLE = 500;

public:
    ServoController(uint pin);

    void init();
    float pulse_to_degrees(uint pulse_us) const;
    void set_pulse_us(uint pulse_us);
    void move_to_next_position();
    bool check_complete_lidar_rotation(float current_angle);
    bool should_move_servo() const;
    float get_current_angle() const;
    void reset_sampling_state();
};

#endif // SERVO_CONTROLLER_HPP