"""Data Update Coordinator for SmartGrade integration."""
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api_client import SmartGradeAPIClient, TokenExpiredError
from .const import DOMAIN, SCAN_INTERVAL, SCAN_INTERVAL_MQTT
from .mqtt_client import SmartGradeMQTTClient
from .token_manager import TokenManager

_LOGGER = logging.getLogger(__name__)


class SmartGradeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching SmartGrade data from API.
    
    Handles both HTTP API polling and real-time MQTT updates.
    Uses hybrid strategy: MQTT for device state, HTTP for timers/schedules.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api: SmartGradeAPIClient,
        mqtt: SmartGradeMQTTClient | None,
        token_mgr: TokenManager,
    ):
        """Initialize coordinator.
        
        Args:
            hass: Home Assistant instance
            api: SmartGrade API client
            mqtt: MQTT client (optional, None if MQTT failed to connect)
            token_mgr: Token manager
        """
        # Use different update intervals based on MQTT availability
        update_interval = (
            timedelta(seconds=SCAN_INTERVAL_MQTT)
            if mqtt and mqtt.is_connected
            else timedelta(seconds=SCAN_INTERVAL)
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        
        self.api = api
        self.mqtt = mqtt
        self.token_mgr = token_mgr
        
        # Register MQTT callback if available
        if self.mqtt:
            self.mqtt.register_callback(self._handle_mqtt_message)
            _LOGGER.info(
                "MQTT connected - using %ds polling interval for timers/schedules",
                SCAN_INTERVAL_MQTT,
            )
        else:
            _LOGGER.info(
                "MQTT not available - using %ds HTTP polling interval",
                SCAN_INTERVAL,
            )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API.
        
        Returns:
            Dictionary with device data keyed by device ID
            
        Raises:
            UpdateFailed: If update fails
        """
        try:
            # Check token expiration before making API calls
            await self.token_mgr.check_expiration()
            
            # Fetch all devices
            devices = await self.api.async_get_devices()
            
            # Build device data dictionary
            device_data = {}
            for device in devices:
                device_id = device.get("id")
                if not device_id:
                    _LOGGER.warning("Device missing ID, skipping: %s", device)
                    continue
                
                # Extract switch states
                switches = {}
                if "switch_1" in device:
                    switches["switch_1"] = device.get("switch_1", False)
                if "switch_2" in device:
                    switches["switch_2"] = device.get("switch_2", False)
                if "switch_3" in device:
                    switches["switch_3"] = device.get("switch_3", False)
                
                # Fetch timers for this device
                try:
                    timers = await self.api.async_get_device_timers(device_id)
                except Exception as err:
                    _LOGGER.debug(
                        "Failed to get timers for device %s: %s", device_id, err
                    )
                    timers = []
                
                device_data[device_id] = {
                    "id": device_id,
                    "name": device.get("name", "Unknown Device"),
                    "mac": device.get("mac", ""),
                    "type": device.get("type", "switch"),
                    "site_id": device.get("site_id", ""),
                    "site_name": device.get("site_name", ""),
                    "switches": switches,
                    "online": device.get("online", True),
                    "timers": timers,
                    "raw": device,  # Keep raw data for reference
                }
            
            _LOGGER.debug("Updated data for %d devices", len(device_data))
            return device_data
            
        except TokenExpiredError:
            # Token expired - trigger repair flow
            _LOGGER.error("Token expired during data update")
            await self.token_mgr.trigger_repair_flow()
            raise UpdateFailed("Token expired - re-authentication required")
        
        except Exception as err:
            _LOGGER.exception("Error fetching SmartGrade data: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}") from err

    def _handle_mqtt_message(
        self, device_id: str, message_type: str, payload: dict[str, Any]
    ) -> None:
        """Handle real-time MQTT updates.
        
        Args:
            device_id: Device ID (MAC address)
            message_type: Message type ('power' or 'sensor')
            payload: Message payload
        """
        if not self.data:
            _LOGGER.debug("No data yet, ignoring MQTT message")
            return
        
        # Find device in our data
        device = None
        for dev_id, dev_data in self.data.items():
            if dev_data.get("mac") == device_id or dev_id == device_id:
                device = dev_data
                break
        
        if not device:
            _LOGGER.debug("Device %s not found in coordinator data", device_id)
            return
        
        # Update device state based on message type
        if message_type == "power":
            # Update switch states from MQTT
            if "switch_1" in payload:
                device["switches"]["switch_1"] = payload["switch_1"]
            if "switch_2" in payload:
                device["switches"]["switch_2"] = payload["switch_2"]
            if "switch_3" in payload:
                device["switches"]["switch_3"] = payload["switch_3"]
            
            _LOGGER.debug(
                "Updated device %s switches from MQTT: %s",
                device_id,
                device["switches"],
            )
            
            # Notify listeners of the update
            self.async_set_updated_data(self.data)
        
        elif message_type == "sensor":
            # Handle sensor data (energy, temperature, etc.)
            _LOGGER.debug("Received sensor data for device %s: %s", device_id, payload)
            # TODO: Store sensor data if needed

    async def async_shutdown(self) -> None:
        """Shutdown coordinator and cleanup resources."""
        if self.mqtt:
            await self.mqtt.async_disconnect()
        _LOGGER.info("SmartGrade coordinator shut down")
