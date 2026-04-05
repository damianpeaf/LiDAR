#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/pwm.h"

#define SERVO_PIN 10

// Convierte un ángulo (0° a 180°) en un pulso entre 1.0ms y 2.0ms
float angle_to_pulse_ms(int angle)
{
    return 0.5f + (angle / 180.0f) * 2.0f; // Por ejemplo: 0.5ms–2.5ms si el servo lo tolera
}

void set_servo_angle(uint pin, int angle)
{
    uint slice = pwm_gpio_to_slice_num(pin);
    float ms = angle_to_pulse_ms(angle);
    float duty = (ms / 20.0f) * (pwm_hw->slice[slice].top + 1);
    pwm_set_gpio_level(pin, (uint16_t)duty);
}

int main()
{
    stdio_init_all();

    gpio_set_function(SERVO_PIN, GPIO_FUNC_PWM);
    uint slice_num = pwm_gpio_to_slice_num(SERVO_PIN);

    pwm_config config = pwm_get_default_config();
    pwm_config_set_clkdiv(&config, 64.f); // Divisor de reloj
    pwm_config_set_wrap(&config, 39062);  // 125MHz / 64 / 50Hz
    pwm_init(slice_num, &config, true);

    while (true)
    {
        // Subida: 0° a 180°
        for (int angle = 0; angle <= 180; angle += 1)
        {
            set_servo_angle(SERVO_PIN, angle);
            printf("Ángulo actual: %d°\n", angle);
            sleep_ms(15); // Ajusta según la velocidad del servo
        }

        // Bajada: 180° a 0°
        for (int angle = 180; angle >= 0; angle -= 1)
        {
            set_servo_angle(SERVO_PIN, angle);
            printf("Ángulo actual: %d°\n", angle);
            sleep_ms(15);
        }

        sleep_ms(1000); // Pausa entre ciclos
    }
}
