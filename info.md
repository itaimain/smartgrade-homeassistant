# SmartGrade Integration for Home Assistant

Control your SmartGrade smart switches and water heaters directly from Home Assistant!

## Features

- **Switch Control**: Turn devices on/off from Home Assistant
- **Real-time Updates**: MQTT-based instant state changes
- **Timer Management**: Create and manage device timers
- **Energy Monitoring**: Track kWh consumption
- **Token Management**: Automatic expiration warnings

## Quick Start

1. Install via HACS
2. Add integration via Settings → Devices & Services
3. Enter your Israeli phone number
4. Enter SMS verification code
5. Your devices will appear automatically!

## Token Expiration

SmartGrade tokens expire after 30 days. You'll receive:
- Warning notification 3 days before expiration
- Repair notification when expired
- Easy re-authentication flow

## Services

### Create Timer
```yaml
service: smartgrade.create_timer
data:
  device_id: switch.smartgrade_water_heater
  time: "08:00"
  action: "on"
  days: [monday, tuesday, wednesday, thursday, friday]
```

### Delete Timer
```yaml
service: smartgrade.delete_timer
data:
  device_id: switch.smartgrade_water_heater
  timer_id: "timer_123456"
```

## Support

- [GitHub Issues](https://github.com/itaimain/homeassistant-smartgrade/issues)
- [Documentation](https://github.com/itaimain/homeassistant-smartgrade)
