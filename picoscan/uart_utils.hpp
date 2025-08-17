#ifndef UART_UTILS_HPP
#define UART_UTILS_HPP

#include "pico/stdlib.h"
#include "hardware/uart.h"

bool uart_read_byte_timeout(uart_inst_t *uart, uint8_t *byte, uint32_t timeout_ms);
bool uart_read_bytes_timeout(uart_inst_t *uart, uint8_t *buffer, size_t len, uint32_t timeout_ms);
void uart_clear_buffer(uart_inst_t *uart);

#endif // UART_UTILS_HPP
