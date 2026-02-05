# SmartGrade Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Home Assistant custom integration for SmartGrade smart switches and water heaters.

## Features

- **Switch Control**: Turn water heaters and switches on/off
- **Real-time Updates**: 
  - Instant updates when controlling from Home Assistant (via MQTT)
  - 10-second polling for changes made in the SmartGrade app
- **Energy Monitoring**: Track kWh consumption (if supported by device)
- **Timer Management**: Create/delete timers via services
- **Device Status**: Monitor online/offline status
- **Multi-switch Support**: Control devices with up to 3 switches
- **Token Management**: Automatic expiration warnings and re-authentication flow

## Requirements

- Home Assistant 2023.1 or newer
- SmartGrade account with Israeli phone number
- Access to SMS for authentication

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install" on the SmartGrade integration
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/smartgrade` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### Initial Setup

1. Go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "SmartGrade"
4. Enter your Israeli phone number (e.g., 0501234567)
5. Wait for SMS verification code
6. Enter the 4-digit code
7. Your devices will be automatically discovered

### Token Expiration

SmartGrade JWT tokens expire after **30 days**. The integration will:

- Show a persistent notification **3 days before expiration**
- Create a repair issue when token expires
- Guide you through re-authentication via SMS

**Re-authentication is required** - there is no automatic token renewal.

## Entities

### Switches

Each device creates switch entities for control:

- `switch.smartgrade_<device_name>` - Main switch
- `switch.smartgrade_<device_name>_switch_2` - Second switch (if available)
- `switch.smartgrade_<device_name>_switch_3` - Third switch (if available)

### Sensors

Each device creates sensor entities:

- `sensor.smartgrade_<device_name>_next_timer` - Next scheduled timer (timestamp)
- `sensor.smartgrade_<device_name>_energy` - Energy consumption (kWh)

## Services

### smartgrade.create_timer

Create a new timer for a device.

```yaml
service: smartgrade.create_timer
data:
  device_id: switch.smartgrade_water_heater
  time: "08:00"
  action: "on"
  days:
    - monday
    - tuesday
    - wednesday
    - thursday
    - friday
```

**Parameters:**

- `device_id` (required): Device ID or entity ID
- `time` (required): Time in HH:MM format
- `action` (required): "on" or "off"
- `days` (optional): List of days (monday, tuesday, etc.)

### smartgrade.delete_timer

Delete an existing timer from a device.

```yaml
service: smartgrade.delete_timer
data:
  device_id: switch.smartgrade_water_heater
  timer_id: "timer_123456"
```

**Parameters:**

- `device_id` (required): Device ID or entity ID
- `timer_id` (required): Timer ID to delete

## Automation Examples

### Turn on water heater in the morning

```yaml
automation:
  - alias: "Morning Water Heater"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.smartgrade_water_heater
```

### Notify when token is expiring

```yaml
automation:
  - alias: "SmartGrade Token Expiring Notification"
    trigger:
      - platform: event
        event_type: persistent_notifications_updated
        event_data:
          notification_id: smartgrade_token_expiring
    action:
      - service: notify.mobile_app
        data:
          title: "SmartGrade Re-authentication Needed"
          message: "Your SmartGrade token is expiring soon. Please re-authenticate."
```

### Create weekly timer for water heater

```yaml
automation:
  - alias: "Setup Weekly Water Heater Timer"
    trigger:
      - platform: homeassistant
        event: start
    action:
      - service: smartgrade.create_timer
        data:
          device_id: switch.smartgrade_water_heater
          time: "07:00"
          action: "on"
          days:
            - monday
            - tuesday
            - wednesday
            - thursday
            - friday
```

## Known Limitations

### MQTT Update Direction

- **Home Assistant → Device**: ✅ Instant updates via MQTT
- **Device → Home Assistant**: ✅ Instant updates via MQTT  
- **SmartGrade App → Home Assistant**: ⏱️ 10-second polling delay

The SmartGrade app does not publish its state changes to MQTT, so Home Assistant relies on HTTP polling to detect app-initiated changes. This results in a 10-15 second delay when you control devices from the official app.

**Recommendation:** Use Home Assistant as your primary control interface for instant feedback.

## Troubleshooting

### Devices not updating immediately

**Problem:** Changes made in the SmartGrade app take 10-15 seconds to appear in Home Assistant.

**Explanation:** This is expected behavior. The SmartGrade app does not publish state changes to MQTT when you control devices from the app itself. Home Assistant polls the API every 10 seconds to detect external changes.

**Note:** Changes made FROM Home Assistant are instant (via MQTT), only changes made IN the app have this delay.

**Solutions:**

1. Accept the 10-second polling delay for app-initiated changes
2. Use Home Assistant as your primary control interface for instant updates
3. Check logs if the delay is longer than 10-15 seconds:
   ```
   Settings > System > Logs
   Search for "smartgrade"
   ```

3. Restart the integration:
   ```
   Settings > Devices & Services > SmartGrade > ... > Reload
   ```

### Token expired error

**Problem:** "Token expired - re-authentication required" error.

**Solutions:**

1. This is normal behavior after 30 days
2. Go to **Settings** > **Devices & Services**
3. Click on the SmartGrade integration
4. Follow the re-authentication flow
5. Enter your phone number and SMS code

### Cannot connect error during setup

**Problem:** "Failed to connect to SmartGrade API" error.

**Solutions:**

1. Check your internet connection
2. Verify your phone number is correct (Israeli format: 0501234567)
3. Wait a few minutes and try again (rate limiting)
4. Check Home Assistant logs for detailed error messages

### Invalid SMS code

**Problem:** "Invalid SMS code" error during authentication.

**Solutions:**

1. Double-check the 4-digit code from your SMS
2. Make sure you're entering the most recent code
3. Request a new code if the old one expired
4. Check for extra spaces when copying the code

### Energy sensor shows "unavailable"

**Problem:** Energy sensor is unavailable or shows no data.

**Solutions:**

1. Energy monitoring is only supported by certain devices (water heaters, boilers)
2. Check if your device type supports energy monitoring in the SmartGrade app
3. The sensor will show "unavailable" if not supported

## Technical Details

### Communication

- **HTTP API**: `https://api.iotechv.com`
  - Authentication (phone + SMS)
  - Device control
  - Timer management
  - Energy data

- **MQTT Broker**: `vernemq.iotechv.com` (63.32.36.56:1883)
  - Real-time device state updates
  - Non-TLS connection
  - Username: User ID
  - Password: JWT token

### Update Strategy

- **With MQTT**: Real-time state updates + 5-minute HTTP polling for timers
- **Without MQTT**: 30-second HTTP polling for all data

### Token Lifecycle

1. Initial authentication: Phone number + SMS code → JWT token (30-day lifetime)
2. Days 1-27: Normal operation
3. Day 28: Warning notification appears
4. Day 30: Token expires, repair issue created
5. Re-authentication required: Same SMS flow

## Support

- **Issues**: [GitHub Issues](https://github.com/itaimain/smartgrade-homeassistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/itaimain/smartgrade-homeassistant/discussions)

## Credits

Developed through reverse engineering of the SmartGrade mobile app. All authentication credentials and API endpoints were discovered through APK analysis.

## License

MIT License - see LICENSE file for details
