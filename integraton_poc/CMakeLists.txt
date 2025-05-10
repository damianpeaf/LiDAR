# Generated Cmake Pico project file for integraton_poc

cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Initialise pico_sdk from installed location
# (note this can come from environment, CMake cache etc)

# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.1.1)
set(toolchainVersion 14_2_Rel1)
set(picotoolVersion 2.1.1)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================
set(PICO_BOARD pico2 CACHE STRING "Board type")

# Pull in Raspberry Pi Pico SDK (must be before project)
include(pico_sdk_import.cmake)

project(integraton_poc C CXX ASM)

# Initialise the Raspberry Pi Pico SDK
pico_sdk_init()

# Add executable. Default name is the project name, version 0.1
add_executable(integraton_poc
    integraton_poc.c
)

pico_set_program_name(integraton_poc "integraton_poc")
pico_set_program_version(integraton_poc "0.1")

# Configuración de salida por UART/USB
# Habilitamos ambos como en el proyecto tf_poc
pico_enable_stdio_uart(integraton_poc 1)
pico_enable_stdio_usb(integraton_poc 1)

# Add the standard library to the build
# Combinamos las bibliotecas de ambos proyectos
target_link_libraries(integraton_poc
    pico_stdlib
    hardware_pwm     # De motors_poc
    hardware_uart    # De tf_poc
)

# Add the standard include files to the build
target_include_directories(integraton_poc PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
)

pico_add_extra_outputs(integraton_poc)