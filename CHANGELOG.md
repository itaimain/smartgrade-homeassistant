# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-02-05

### Fixed
- Fixed device discovery issue by using correct API endpoint `/api/v1/users/{user_id}/sites` instead of `/api/v1/sites`
- Corrected query parameter from `withShared` to `shared` to match API specification
- Devices will now be properly discovered during integration setup

## [1.0.0] - 2026-02-05

### Added
- Initial release
- Phone number + SMS authentication
- JWT token management with expiration monitoring
- Switch entities for device control
- Multi-switch support (up to 3 switches per device)
- Real-time MQTT updates
- HTTP API fallback when MQTT unavailable
- Timer management services (create/delete)
- Next timer sensor (timestamp)
- Energy consumption sensor (kWh)
- Token expiration warnings (3 days before)
- Automatic repair flow on token expiration
- Re-authentication flow
- Device grouping by site
- Comprehensive error handling
- Detailed logging

### Features
- **Authentication**: Phone + SMS with JWT tokens (30-day lifecycle)
- **Device Control**: Switch entities with instant state updates
- **Real-time Updates**: MQTT client with automatic reconnection
- **Monitoring**: Timer status and energy consumption sensors
- **Services**: Create and delete device timers
- **User Experience**: Config flow, notifications, and repair flow

### Technical
- Async/await throughout
- Coordinator pattern for data management
- Hybrid MQTT/HTTP update strategy
- Proper Home Assistant integration standards
- Comprehensive documentation
- HACS compatible

[1.0.1]: https://github.com/itaimain/smartgrade-homeassistant/releases/tag/v1.0.1
[1.0.0]: https://github.com/itaimain/homeassistant-smartgrade/releases/tag/v1.0.0
