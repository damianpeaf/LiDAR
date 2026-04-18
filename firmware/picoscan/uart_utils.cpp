#include "uart_utils.hpp"

#include "hardware/irq.h"

namespace
{
constexpr size_t UART_RX_RING_BUFFER_SIZE = 2048;

struct UartRxRingBufferContext
{
    uart_inst_t *uart;
    volatile uint16_t head;
    volatile uint16_t tail;
    volatile uint32_t overflow_count;
    volatile uint16_t max_backlog;
    volatile bool initialized;
    uint8_t buffer[UART_RX_RING_BUFFER_SIZE];
};

UartRxRingBufferContext uart_contexts[] = {
    {uart0, 0, 0, 0, 0, false, {0}},
    {uart1, 0, 0, 0, 0, false, {0}},
};

uint16_t uart_ring_backlog(const UartRxRingBufferContext &context)
{
    if (context.head >= context.tail)
    {
        return static_cast<uint16_t>(context.head - context.tail);
    }

    return static_cast<uint16_t>(UART_RX_RING_BUFFER_SIZE - context.tail + context.head);
}

UartRxRingBufferContext *uart_get_context(uart_inst_t *uart)
{
    for (auto &context : uart_contexts)
    {
        if (context.uart == uart)
        {
            return &context;
        }
    }

    return nullptr;
}

void uart_drain_hardware_fifo(uart_inst_t *uart)
{
    while (uart_is_readable(uart))
    {
        uart_getc(uart);
    }
}

void uart_on_rx_irq(UartRxRingBufferContext &context)
{
    while (uart_is_readable(context.uart))
    {
        const uint8_t byte = uart_getc(context.uart);
        const uint16_t next_head = (context.head + 1) % UART_RX_RING_BUFFER_SIZE;

        if (next_head == context.tail)
        {
            context.overflow_count++;
            continue;
        }

        context.buffer[context.head] = byte;
        context.head = next_head;

        const uint16_t backlog = uart_ring_backlog(context);
        if (backlog > context.max_backlog)
        {
            context.max_backlog = backlog;
        }
    }
}

void uart0_rx_irq_handler()
{
    uart_on_rx_irq(uart_contexts[0]);
}

void uart1_rx_irq_handler()
{
    uart_on_rx_irq(uart_contexts[1]);
}

bool uart_read_byte_from_ring_buffer(UartRxRingBufferContext *context, uint8_t *byte)
{
    if (context == nullptr || !context->initialized || context->head == context->tail)
    {
        return false;
    }

    *byte = context->buffer[context->tail];
    context->tail = (context->tail + 1) % UART_RX_RING_BUFFER_SIZE;
    return true;
}

bool uart_read_byte_from_hardware_until(uart_inst_t *uart, uint8_t *byte, absolute_time_t deadline)
{
    while (!time_reached(deadline))
    {
        if (uart_is_readable(uart))
        {
            *byte = uart_getc(uart);
            return true;
        }

        tight_loop_contents();
    }

    if (uart_is_readable(uart))
    {
        *byte = uart_getc(uart);
        return true;
    }

    return false;
}
} // namespace

static bool uart_read_byte_until(uart_inst_t *uart, uint8_t *byte, absolute_time_t deadline)
{
    UartRxRingBufferContext *context = uart_get_context(uart);

    if (context != nullptr && context->initialized)
    {
        while (!time_reached(deadline))
        {
            if (uart_read_byte_from_ring_buffer(context, byte))
            {
                return true;
            }

            tight_loop_contents();
        }

        return uart_read_byte_from_ring_buffer(context, byte);
    }

    return uart_read_byte_from_hardware_until(uart, byte, deadline);
}

void uart_init_rx_irq_ring_buffer(uart_inst_t *uart)
{
    UartRxRingBufferContext *context = uart_get_context(uart);
    if (context == nullptr)
    {
        return;
    }

    uart_set_irq_enables(uart, false, false);
    context->head = 0;
    context->tail = 0;
    context->overflow_count = 0;
    context->max_backlog = 0;
    context->initialized = true;
    uart_drain_hardware_fifo(uart);

    const uint irq_number = uart == uart0 ? UART0_IRQ : UART1_IRQ;
    irq_set_exclusive_handler(irq_number, uart == uart0 ? uart0_rx_irq_handler : uart1_rx_irq_handler);
    irq_set_enabled(irq_number, true);
    uart_set_irq_enables(uart, true, false);
}

bool uart_read_byte_timeout(uart_inst_t *uart, uint8_t *byte, uint32_t timeout_ms)
{
    return uart_read_byte_until(uart, byte, make_timeout_time_ms(timeout_ms));
}

bool uart_read_bytes_timeout(uart_inst_t *uart, uint8_t *buffer, size_t len, uint32_t timeout_ms)
{
    absolute_time_t deadline = make_timeout_time_ms(timeout_ms);

    for (size_t i = 0; i < len; i++)
    {
        if (!uart_read_byte_until(uart, &buffer[i], deadline))
        {
            return false;
        }
    }
    return true;
}

void uart_clear_buffer(uart_inst_t *uart)
{
    UartRxRingBufferContext *context = uart_get_context(uart);
    if (context != nullptr)
    {
        context->head = 0;
        context->tail = 0;
    }

    uart_drain_hardware_fifo(uart);
}

uint32_t uart_get_rx_overflow_count(uart_inst_t *uart)
{
    UartRxRingBufferContext *context = uart_get_context(uart);
    return context != nullptr ? context->overflow_count : 0;
}

uint16_t uart_get_rx_ring_backlog(uart_inst_t *uart)
{
    UartRxRingBufferContext *context = uart_get_context(uart);
    return context != nullptr ? uart_ring_backlog(*context) : 0;
}

uint16_t uart_get_rx_ring_max_backlog(uart_inst_t *uart)
{
    UartRxRingBufferContext *context = uart_get_context(uart);
    return context != nullptr ? context->max_backlog : 0;
}
