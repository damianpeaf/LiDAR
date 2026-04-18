#include "servo_controller.hpp"
#include <cstdio>
#include <cmath>

ServoController::ServoController(uint pin) 
    : gpio_pin(pin), current_pulse(SERVO_MIN_PULSE), direction(1),
      samples_collected(0), points_in_sample(0), last_lidar_angle(-1.0f),
      waiting_for_rotation(false), state(State::Sampling), settle_deadline(nil_time)
{
}

void ServoController::update() {}

void ServoController::init()
{
    gpio_set_function(gpio_pin, GPIO_FUNC_PWM);
    slice_num = pwm_gpio_to_slice_num(gpio_pin);

    float clock_div = 40.0f;
    pwm_set_clkdiv(slice_num, clock_div);
    wrap_value = 62500 - 1;
    pwm_set_wrap(slice_num, wrap_value);
    pwm_set_enabled(slice_num, true);
    
    set_pulse_us(current_pulse);
}

void ServoController::update()
{
    if (state == State::Settling && time_reached(settle_deadline))
    {
        state = State::Sampling;
        printf("Servo settled at %.1f degrees, resuming sampling...\n",
               pulse_to_degrees(current_pulse));
    }
}

float ServoController::pulse_to_degrees(uint pulse_us) const
{
    return (float)(pulse_us - SERVO_MIN_PULSE) * 180.0f / (SERVO_MAX_PULSE - SERVO_MIN_PULSE);
}

void ServoController::set_pulse_us(uint pulse_us)
{
    uint16_t level = (pulse_us * wrap_value) / 20000;
    pwm_set_gpio_level(gpio_pin, level);
}

void ServoController::move_to_next_position()
{
    current_pulse += direction * SERVO_STEP_SIZE;

    if (current_pulse >= SERVO_MAX_PULSE)
    {
        current_pulse = SERVO_MAX_PULSE;
        direction = -1;
    }
    else if (current_pulse <= SERVO_MIN_PULSE)
    {
        current_pulse = SERVO_MIN_PULSE;
        direction = 1;
    }

    set_pulse_us(current_pulse);
    reset_sampling_state();
    state = State::Settling;
    settle_deadline = make_timeout_time_ms(SERVO_SETTLE_MS);

    printf("Servo moved to pulse %d (%.1f degrees), settling...\n",
           current_pulse, pulse_to_degrees(current_pulse));
}

bool ServoController::check_complete_lidar_rotation(float current_angle)
{
    if (!is_ready_for_sampling())
    {
        return false;
    }

    if (!waiting_for_rotation)
    {
        waiting_for_rotation = true;
        last_lidar_angle = current_angle;
        points_in_sample = 1;
        return false;
    }

    points_in_sample++;

    if (points_in_sample >= MIN_POINTS_PER_SAMPLE)
    {
        float angle_diff = fabs(current_angle - last_lidar_angle);
        if (angle_diff < 10.0f || angle_diff > 350.0f)
        {
            samples_collected++;
            int completed_points = points_in_sample;
            points_in_sample = 0;
            waiting_for_rotation = false;

            printf("Sample %d completed at servo angle %.1f degrees (%d points)\n",
                   samples_collected, pulse_to_degrees(current_pulse), completed_points);

            return true;
        }
    }

    return false;
}

bool ServoController::should_move_servo() const
{
    return is_ready_for_sampling() && samples_collected >= SAMPLES_PER_POSITION;
}

float ServoController::get_current_angle() const
{
    return pulse_to_degrees(current_pulse);
}

bool ServoController::is_ready_for_sampling() const
{
    return state == State::Sampling;
}

void ServoController::reset_sampling_state()
{
    samples_collected = 0;
    points_in_sample = 0;
    last_lidar_angle = -1.0f;
    waiting_for_rotation = false;
}
