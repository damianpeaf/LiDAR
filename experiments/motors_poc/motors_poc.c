#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/pwm.h"

// ---- Servo configuration ----
#define SERVO_PIN 10

float angle_to_pulse_ms(int angle)
{
    return 0.5f + (angle / 180.0f) * 2.0f;
}

void set_servo_angle(uint pin, int angle)
{
    uint slice = pwm_gpio_to_slice_num(pin);
    float ms = angle_to_pulse_ms(angle);
    float duty = (ms / 20.0f) * (pwm_hw->slice[slice].top + 1);
    pwm_set_gpio_level(pin, (uint16_t)duty);
}

void init_servo(uint pin)
{
    gpio_set_function(pin, GPIO_FUNC_PWM);
    uint slice_num = pwm_gpio_to_slice_num(pin);
    pwm_config config = pwm_get_default_config();
    pwm_config_set_clkdiv(&config, 64.f);
    pwm_config_set_wrap(&config, 39062); // 50Hz PWM
    pwm_init(slice_num, &config, true);
}

// ---- Stepper configuration ----
#define IN1 4
#define IN2 5
#define IN3 6
#define IN4 7

const uint8_t half_step_sequence[8][4] = {
    {1, 0, 0, 0},
    {1, 1, 0, 0},
    {0, 1, 0, 0},
    {0, 1, 1, 0},
    {0, 0, 1, 0},
    {0, 0, 1, 1},
    {0, 0, 0, 1},
    {1, 0, 0, 1}};

#define DELAY_MS 1
#define HALF_STEPS_PER_180 4076
#define STEPS_PER_DEGREE (HALF_STEPS_PER_180 / 180)
#define MAX_VERTICAL_ANGLE 60
#define SENSOR_WAIT_MS 200

static int step_index = 0;

void step_motor(int step)
{
    gpio_put(IN1, half_step_sequence[step][0]);
    gpio_put(IN2, half_step_sequence[step][1]);
    gpio_put(IN3, half_step_sequence[step][2]);
    gpio_put(IN4, half_step_sequence[step][3]);
}

void rotate_halfsteps(int steps, bool clockwise)
{
    for (int i = 0; i < steps; i++)
    {
        if (clockwise)
        {
            step_index = (step_index + 1) % 8;
        }
        else
        {
            step_index = (step_index + 7) % 8;
        }
        step_motor(step_index);
        sleep_ms(DELAY_MS);
    }
}

void init_stepper()
{
    gpio_init(IN1);
    gpio_set_dir(IN1, GPIO_OUT);
    gpio_init(IN2);
    gpio_set_dir(IN2, GPIO_OUT);
    gpio_init(IN3);
    gpio_set_dir(IN3, GPIO_OUT);
    gpio_init(IN4);
    gpio_set_dir(IN4, GPIO_OUT);
}

// ---- Grid scan ----
void horizontal_scan_line(bool clockwise)
{
    for (int i = 0; i < 180; i++)
    {
        rotate_halfsteps(STEPS_PER_DEGREE, clockwise);
        sleep_ms(SENSOR_WAIT_MS); // Simula tiempo de captura del sensor
    }
}

int main()
{
    stdio_init_all();
    init_stepper();
    init_servo(SERVO_PIN);

    // --- Posición inicial ---
    set_servo_angle(SERVO_PIN, 0);
    sleep_ms(500);

    rotate_halfsteps(HALF_STEPS_PER_180, false); // Garantiza que esté en 0°
    sleep_ms(500);

    // --- Escaneo tipo grilla ---
    for (int vertical_angle = 0; vertical_angle <= MAX_VERTICAL_ANGLE; vertical_angle += 10)
    {
        set_servo_angle(SERVO_PIN, vertical_angle);
        sleep_ms(300); // Estabilización del servo

        bool clockwise = (vertical_angle / 10) % 2 == 0;
        horizontal_scan_line(clockwise);

        sleep_ms(100); // Pausa corta entre líneas
    }

    // --- Regresar todo al inicio ---
    set_servo_angle(SERVO_PIN, 0);
    sleep_ms(300);

    rotate_halfsteps(HALF_STEPS_PER_180, false); // Vuelve horizontalmente a 0°
    sleep_ms(300);

    return 0;
}
