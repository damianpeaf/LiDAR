#pragma once

enum class DeviceState {
    BOOT,
    CONNECTING_WIFI,
    WIFI_READY,
    CONNECTING_CLOUD,
    IDLE,
    SCANNING,
    ERROR
};

class DeviceStateManager {
public:
    DeviceStateManager();

    DeviceState get_state() const;
    void transition_to(DeviceState next);
    const char* state_name() const;

    bool is_cloud_ready() const;
    bool is_scanning() const;

    static const char* name_of(DeviceState s);

private:
    DeviceState state_;
};
