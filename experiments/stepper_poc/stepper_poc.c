#include "pico/stdlib.h"

#define IN1 4
#define IN2 5
#define IN3 6
#define IN4 7

// Secuencia de medio paso (Half-Step)
const uint8_t half_step_sequence[8][4] = {
    {1, 0, 0, 0},
    {1, 1, 0, 0},
    {0, 1, 0, 0},
    {0, 1, 1, 0},
    {0, 0, 1, 0},
    {0, 0, 1, 1},
    {0, 0, 0, 1},
    {1, 0, 0, 1}};

#define HALF_STEPS_PER_180 4076
#define DELAY_MS 2 // Menor = más rápido

void step_motor(int step)
{
    gpio_put(IN1, half_step_sequence[step][0]);
    gpio_put(IN2, half_step_sequence[step][1]);
    gpio_put(IN3, half_step_sequence[step][2]);
    gpio_put(IN4, half_step_sequence[step][3]);
}

void rotate_halfsteps(int total_steps, bool clockwise)
{
    static int step_index = 0;
    for (int i = 0; i < total_steps; i++)
    {
        if (clockwise)
        {
            step_index = (step_index + 1) % 8;
        }
        else
        {
            step_index = (step_index + 7) % 8; // -1 mod 8
        }
        step_motor(step_index);
        sleep_ms(DELAY_MS);
    }
}

int main()
{
    stdio_init_all();

    gpio_init(IN1);
    gpio_set_dir(IN1, GPIO_OUT);
    gpio_init(IN2);
    gpio_set_dir(IN2, GPIO_OUT);
    gpio_init(IN3);
    gpio_set_dir(IN3, GPIO_OUT);
    gpio_init(IN4);
    gpio_set_dir(IN4, GPIO_OUT);

    while (true)
    {
        rotate_halfsteps(HALF_STEPS_PER_180, true); // 180° horario
        sleep_ms(1000);
        rotate_halfsteps(HALF_STEPS_PER_180, false); // 180° antihorario
        sleep_ms(1000);
    }

    return 0;
}
