#include <cstdio>
#include "device_state_manager.hpp"

DeviceStateManager::DeviceStateManager() : state_(DeviceState::BOOT) {}

DeviceState DeviceStateManager::get_state() const { return state_; }

void DeviceStateManager::transition_to(DeviceState next)
{
    printf("[device] %s → %s\n", state_name(), DeviceStateManager::name_of(next));
    state_ = next;
}

const char* DeviceStateManager::state_name() const
{
    return DeviceStateManager::name_of(state_);
}

const char* DeviceStateManager::name_of(DeviceState s)
{
    switch (s) {
        case DeviceState::BOOT:             return "BOOT";
        case DeviceState::SETUP_AP:         return "SETUP_AP";
        case DeviceState::SETUP_PORTAL:     return "SETUP_PORTAL";
        case DeviceState::CONNECTING_WIFI:  return "CONNECTING_WIFI";
        case DeviceState::WIFI_READY:       return "WIFI_READY";
        case DeviceState::CONNECTING_CLOUD: return "CONNECTING_CLOUD";
        case DeviceState::IDLE:             return "IDLE";
        case DeviceState::SCANNING:         return "SCANNING";
        case DeviceState::ERROR:            return "ERROR";
        default:                            return "UNKNOWN";
    }
}

bool DeviceStateManager::is_cloud_ready() const
{
    return state_ == DeviceState::IDLE || state_ == DeviceState::SCANNING;
}

bool DeviceStateManager::is_scanning() const
{
    return state_ == DeviceState::SCANNING;
}

bool DeviceStateManager::is_setup_mode() const
{
    return state_ == DeviceState::SETUP_AP || state_ == DeviceState::SETUP_PORTAL;
}
