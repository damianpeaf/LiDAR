#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"

#define SERVO_PIN 15

// Variables globales
uint slice_num;
uint16_t wrap_value;

// Función para inicializar el PWM
void servo_init(uint gpio_pin)
{
    gpio_set_function(gpio_pin, GPIO_FUNC_PWM);
    slice_num = pwm_gpio_to_slice_num(gpio_pin);

    // Configuración PWM para 50Hz
    float clock_div = 40.0f;
    pwm_set_clkdiv(slice_num, clock_div);
    wrap_value = 62500 - 1;
    pwm_set_wrap(slice_num, wrap_value);
    pwm_set_enabled(slice_num, true);
}

// Función para convertir microsegundos a grados (interpolación lineal)
float pulse_to_degrees(uint pulse_us)
{
    // MG996R: 500μs = 0°, 2500μs = 180°
    // Interpolación lineal: grados = (pulse - 500) * 180 / (2500 - 500)
    return (float)(pulse_us - 500) * 180.0f / 2000.0f;
}

// Función para establecer ancho de pulso en microsegundos
void servo_set_pulse_us(uint gpio_pin, uint pulse_us)
{
    uint16_t level = (pulse_us * wrap_value) / 20000;
    pwm_set_gpio_level(gpio_pin, level);
}

int main()
{
    stdio_init_all();

    printf("\n=== MOVIMIENTO SUAVE CONTINUO SERVO MG996R ===\n");
    printf("Rango: 0° a 180° (500μs a 2500μs)\n");
    printf("Movimiento ultra-suave iniciando en 3 segundos...\n\n");

    // Dar tiempo inicial para prepararse
    sleep_ms(3000);

    servo_init(SERVO_PIN);

    // Ir al centro primero para inicializar
    float center_angle = pulse_to_degrees(1500);
    printf("Posición inicial: Centro (%.1f°)\n", center_angle);
    servo_set_pulse_us(SERVO_PIN, 1500);
    sleep_ms(2000);

    while (true)
    {
        printf("\n--- BARRIDO SUAVE CONTINUO ---\n");

        // Barrido hacia adelante: 0° → 180° (500μs → 2500μs, pasos de 5μs)
        printf("Barrido suave: 0° → 180°...\n");
        for (uint pulse = 500; pulse <= 2500; pulse += 5)
        {
            float current_angle = pulse_to_degrees(pulse);
            servo_set_pulse_us(SERVO_PIN, pulse);
            printf("→ %.2f°\n", current_angle);
            sleep_ms(15); // 15ms entre cada micro-paso
        }

        float max_angle = pulse_to_degrees(2500);
        printf("Alcanzado máximo (%.1f°) - Pausa breve\n", max_angle);
        sleep_ms(1000);

        // Barrido hacia atrás: 180° → 0° (2500μs → 500μs, pasos de 5μs)
        printf("Barrido suave: 180° → 0°...\n");
        for (uint pulse = 2500; pulse >= 500; pulse -= 5)
        {
            float current_angle = pulse_to_degrees(pulse);
            servo_set_pulse_us(SERVO_PIN, pulse);
            printf("← %.2f°\n", current_angle);
            sleep_ms(15); // 15ms entre cada micro-paso
        }

        float min_angle = pulse_to_degrees(500);
        printf("Alcanzado mínimo (%.1f°) - Pausa breve\n", min_angle);
        sleep_ms(1000);

        printf("Ciclo suave completado.\n");
    }

    return 0;
}