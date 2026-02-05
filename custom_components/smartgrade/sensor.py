"""Sensor platform for SmartGrade integration."""
import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartGradeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SmartGrade sensors from a config entry."""
    coordinator: SmartGradeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Create sensor entities for each device
    for device_id, device in coordinator.data.items():
        # Add timer status sensor for devices with timers
        timers = device.get("timers", [])
        if timers or True:  # Always add timer sensor for future use
            entities.append(
                SmartGradeTimerSensor(coordinator, device_id)
            )
        
        # Add energy sensor (will show unavailable if not supported)
        entities.append(
            SmartGradeEnergySensor(coordinator, device_id)
        )
    
    _LOGGER.info("Setting up %d SmartGrade sensor entities", len(entities))
    async_add_entities(entities)


class SmartGradeTimerSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing next scheduled timer for a device."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:timer-outline"

    def __init__(
        self,
        coordinator: SmartGradeDataUpdateCoordinator,
        device_id: str,
    ):
        """Initialize the timer sensor.
        
        Args:
            coordinator: Data update coordinator
            device_id: Device ID
        """
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_next_timer"
        
        # Set entity ID
        device_name = self._get_device().get("name", "Unknown")
        safe_name = device_name.lower().replace(" ", "_")
        self.entity_id = f"sensor.smartgrade_{safe_name}_next_timer"

    def _get_device(self) -> dict[str, Any]:
        """Get device data from coordinator."""
        return self.coordinator.data.get(self._device_id, {})

    @property
    def device_info(self):
        """Return device information for grouping entities."""
        device = self._get_device()
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": device.get("name", "Unknown Device"),
            "manufacturer": "SmartGrade",
            "model": device.get("type", "Switch"),
            "sw_version": "2.0.3",
            "suggested_area": device.get("site_name", ""),
        }

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        device = self._get_device()
        return f"{device.get('name', 'Unknown')} Next Timer"

    @property
    def native_value(self) -> datetime | None:
        """Return the next scheduled timer time."""
        device = self._get_device()
        timers = device.get("timers", [])
        
        if not timers:
            return None
        
        # Find the next timer (earliest scheduled time)
        try:
            next_timer = min(
                timers,
                key=lambda t: t.get("next_run", float("inf")),
            )
            next_run_timestamp = next_timer.get("next_run")
            
            if next_run_timestamp:
                return datetime.fromtimestamp(next_run_timestamp)
        except (ValueError, TypeError, KeyError) as err:
            _LOGGER.debug("Error getting next timer for device %s: %s", self._device_id, err)
        
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        device = self._get_device()
        return device.get("online", False) and self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device = self._get_device()
        timers = device.get("timers", [])
        
        attrs = {
            "total_timers": len(timers),
        }
        
        # Add details of all timers
        if timers:
            timer_list = []
            for timer in timers:
                timer_list.append({
                    "id": timer.get("id"),
                    "time": timer.get("time"),
                    "action": timer.get("action"),
                    "enabled": timer.get("enabled", True),
                    "days": timer.get("days", []),
                })
            attrs["timers"] = timer_list
        
        return attrs


class SmartGradeEnergySensor(CoordinatorEntity, SensorEntity):
    """Sensor showing energy consumption for a device."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:lightning-bolt"

    def __init__(
        self,
        coordinator: SmartGradeDataUpdateCoordinator,
        device_id: str,
    ):
        """Initialize the energy sensor.
        
        Args:
            coordinator: Data update coordinator
            device_id: Device ID
        """
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_energy"
        self._last_kwh: float | None = None
        
        # Set entity ID
        device_name = self._get_device().get("name", "Unknown")
        safe_name = device_name.lower().replace(" ", "_")
        self.entity_id = f"sensor.smartgrade_{safe_name}_energy"

    def _get_device(self) -> dict[str, Any]:
        """Get device data from coordinator."""
        return self.coordinator.data.get(self._device_id, {})

    @property
    def device_info(self):
        """Return device information for grouping entities."""
        device = self._get_device()
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": device.get("name", "Unknown Device"),
            "manufacturer": "SmartGrade",
            "model": device.get("type", "Switch"),
            "sw_version": "2.0.3",
            "suggested_area": device.get("site_name", ""),
        }

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        device = self._get_device()
        return f"{device.get('name', 'Unknown')} Energy"

    @property
    def native_value(self) -> float | None:
        """Return the energy consumption."""
        # Note: Energy data fetching would require additional API calls
        # For now, return None (unavailable) unless device provides it
        device = self._get_device()
        raw_device = device.get("raw", {})
        
        # Check if device provides energy data
        kwh = raw_device.get("total_kwh") or raw_device.get("energy")
        
        if kwh is not None:
            self._last_kwh = float(kwh)
            return self._last_kwh
        
        return self._last_kwh

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        device = self._get_device()
        # Only available if device is online and supports energy monitoring
        if not device.get("online", False) or not self.coordinator.last_update_success:
            return False
        
        # Check if device type supports energy monitoring
        device_type = device.get("type", "").lower()
        return "heater" in device_type or "boiler" in device_type or self._last_kwh is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "device_id": self._device_id,
            "supports_energy_monitoring": self.available,
        }
