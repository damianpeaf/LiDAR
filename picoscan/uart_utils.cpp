#include "uart_utils.hpp"

bool uart_read_byte_timeout(uart_inst_t *uart, uint8_t *byte, uint32_t timeout_ms)
{
    uint32_t start_time = to_ms_since_boot(get_absolute_time());
    while (to_ms_since_boot(get_absolute_time()) - start_time < timeout_ms)
    {
        if (uart_is_readable(uart))
        {
            *byte = uart_getc(uart);
            return true;
        }
        sleep_ms(1);
    }
    return false;
}

bool uart_read_bytes_timeout(uart_inst_t *uart, uint8_t *buffer, size_t len, uint32_t timeout_ms)
{
    for (size_t i = 0; i < len; i++)
    {
        if (!uart_read_byte_timeout(uart, &buffer[i], timeout_ms))
        {
            return false;
        }
    }
    return true;
}

void uart_clear_buffer(uart_inst_t *uart)
{
    while (uart_is_readable(uart))
    {
        uart_getc(uart);
    }
}
