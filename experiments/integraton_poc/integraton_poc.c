#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"

// ---- Configuración servo ----
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

// ---- Configuración stepper ----
#define IN1 4
#define IN2 5
#define IN3 6
#define IN4 7

const uint8_t half_step_sequence[8][4] = {
    {1, 0, 0, 0}, {1, 1, 0, 0}, {0, 1, 0, 0}, {0, 1, 1, 0}, {0, 0, 1, 0}, {0, 0, 1, 1}, {0, 0, 0, 1}, {1, 0, 0, 1}};

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
        step_index = (clockwise) ? (step_index + 1) % 8 : (step_index + 7) % 8;
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

// ---- LiDAR (UART1) ----
#define BAUD_RATE 115200
#define UART_ID1 uart1
#define UART1_TX_PIN 8
#define UART1_RX_PIN 9

typedef struct
{
    unsigned short Header;
    unsigned short Dist;
    unsigned short Strength;
} structLidar;

union unionLidar
{
    unsigned char Byte[9];
    structLidar lidar;
};

unsigned char lidarCounter = 0;
union unionLidar Lidar;

int isLidar(uart_inst_t *uart, union unionLidar *lidar)
{
    int checksum, loop;
    unsigned char serialChar;
    while (uart_is_readable(uart))
    {
        if (lidarCounter > 8)
        {
            lidarCounter = 0;
            return 0;
        }
        serialChar = uart_getc(uart);
        lidar->Byte[lidarCounter] = serialChar;

        switch (lidarCounter++)
        {
        case 0:
        case 1:
            if (serialChar != 0x59)
                lidarCounter = 0;
            break;
        case 8:
            checksum = 0;
            lidarCounter = 0;
            for (loop = 0; loop < 8; loop++)
                checksum += lidar->Byte[loop];
            if ((checksum & 0xff) == serialChar)
            {
                lidar->lidar.Dist = lidar->Byte[2] | (lidar->Byte[3] << 8);
                lidar->lidar.Strength = lidar->Byte[4] | (lidar->Byte[5] << 8);
                return 1;
            }
        }
    }
    return 0;
}

// ---- Escaneo ----
void horizontal_scan_line(bool clockwise, int phi_angle_deg)
{
    for (int i = 0; i < 180; i++)
    {
        rotate_halfsteps(STEPS_PER_DEGREE, clockwise);
        sleep_ms(SENSOR_WAIT_MS);
        if (isLidar(UART_ID1, &Lidar))
        {
            int theta = clockwise ? i : (179 - i);
            printf("{\"r\":%u,\"theta\":%d,\"phi\":%d,\"strength\":%u}\n",
                   Lidar.lidar.Dist, theta, phi_angle_deg, Lidar.lidar.Strength);
        }
    }
}

int main()
{
    stdio_init_all();
    init_stepper();
    init_servo(SERVO_PIN);

    uart_init(UART_ID1, BAUD_RATE);
    gpio_set_function(UART1_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART1_RX_PIN, GPIO_FUNC_UART);

    sleep_ms(1000);
    printf("Sistema de escaneo LIDAR iniciado\n");

    set_servo_angle(SERVO_PIN, 0);
    sleep_ms(500);

    rotate_halfsteps(HALF_STEPS_PER_180, false);
    sleep_ms(500);

    for (int vertical_angle = 0; vertical_angle <= MAX_VERTICAL_ANGLE; vertical_angle += 10)
    {
        set_servo_angle(SERVO_PIN, vertical_angle);
        sleep_ms(300);
        bool clockwise = (vertical_angle / 10) % 2 == 0;
        horizontal_scan_line(clockwise, vertical_angle);
        sleep_ms(100);
    }

    set_servo_angle(SERVO_PIN, 0);
    sleep_ms(300);
    rotate_halfsteps(HALF_STEPS_PER_180, false);
    sleep_ms(300);

    printf("Escaneo completado.\n");
    return 0;
}
