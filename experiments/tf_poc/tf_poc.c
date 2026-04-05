#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "pico/binary_info.h"
#include "hardware/uart.h"
#include "tusb.h"

#define BAUD_RATE 115200
#define UART_ID1 uart1

#define UART1_TX_PIN 8 // pin-6
#define UART1_RX_PIN 9 // pin-7

const uint LED_PIN = 25; // also set LED from gpio.h file
static bool ret;

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
    int loop;
    int checksum;
    unsigned char serialChar;

    while (uart_is_readable(uart))
    {
        if (lidarCounter > 8)
        {
            lidarCounter = 0;
            return 0; // something wrong
        }

        serialChar = uart_getc(uart); // Read a single character to UART.
        lidar->Byte[lidarCounter] = serialChar;

        switch (lidarCounter++)
        {
        case 0:
        case 1:
            if (serialChar != 0x59)
                lidarCounter = 0;
            break;
        case 8: // checksum
            checksum = 0;
            lidarCounter = 0;
            for (loop = 0; loop < 8; loop++)
                checksum += lidar->Byte[loop];
            if ((checksum & 0xff) == serialChar)
            {
                // printf("checksum ok\n");
                lidar->lidar.Dist = lidar->Byte[2] | lidar->Byte[3] << 8;
                lidar->lidar.Strength = lidar->Byte[4] | lidar->Byte[5] << 8;
                return 1;
            }
            // printf("bad checksum %02x != %02x\n",checksum & 0xff, serialChar);
        }
    }
    return 0;
}

int main()
{

    bi_decl(bi_program_description("This is a program to read from UART!"));
    bi_decl(bi_1pin_with_name(LED_PIN, "On-board LED"));

    bi_decl(bi_1pin_with_name(UART1_TX_PIN, "pin-5 for uart1 TX"));
    bi_decl(bi_1pin_with_name(UART1_RX_PIN, "pin-6 for uart1 RX"));

    // Enable UART so we can print status output
    stdio_init_all();

    gpio_init(LED_PIN);              // initialize pin-25
    gpio_set_dir(LED_PIN, GPIO_OUT); // set pin-25 in output mode

    // Set up our UARTs with the required speed.
    uart_init(UART_ID1, BAUD_RATE);

    gpio_set_function(UART1_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART1_RX_PIN, GPIO_FUNC_UART);

    cdcd_init();
    printf("waiting for usb host");
    while (!tud_cdc_connected())
    {
        printf(".");
        sleep_ms(500);
    }
    printf("\nusb host detected!\n");

    sleep_ms(5000);
    ret = uart_is_enabled(uart1); // pass UART_ID1 or uart1 both are okay
    if (ret == true)
    {
        printf("UART-1 is enabled\n");
    }

    printf("Ready to read data from Benewake LiDAR\n");
    while (true)
    {
        gpio_put(LED_PIN, 0);
        sleep_ms(100);
        gpio_put(LED_PIN, 1);
        if (isLidar(UART_ID1, &Lidar))
        {
            printf("Dist:%u Strength:%u \n",
                   Lidar.lidar.Dist,
                   Lidar.lidar.Strength);
        }
    }
    return 0;
}