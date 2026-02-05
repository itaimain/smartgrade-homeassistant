"""Switch platform for SmartGrade integration."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up SmartGrade switches from a config entry."""
    coordinator: SmartGradeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Create switch entities for each device's switches
    for device_id, device in coordinator.data.items():
        switches = device.get("switches", {})
        
        # Create entities for each switch
        for switch_key, switch_state in switches.items():
            # Extract switch number from key (e.g., "switch_1" -> 1)
            switch_num = int(switch_key.split("_")[1])
            entities.append(
                SmartGradeSwitchEntity(coordinator, device_id, switch_num)
            )
    
    _LOGGER.info("Setting up %d SmartGrade switch entities", len(entities))
    async_add_entities(entities)


class SmartGradeSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Representation of a SmartGrade switch."""

    def __init__(
        self,
        coordinator: SmartGradeDataUpdateCoordinator,
        device_id: str,
        switch_num: int,
    ):
        """Initialize the switch.
        
        Args:
            coordinator: Data update coordinator
            device_id: Device ID
            switch_num: Switch number (1, 2, or 3)
        """
        super().__init__(coordinator)
        self._device_id = device_id
        self._switch_num = switch_num
        self._attr_unique_id = f"{device_id}_switch_{switch_num}"
        
        # Set entity ID
        device_name = self._get_device().get("name", "Unknown")
        safe_name = device_name.lower().replace(" ", "_")
        self.entity_id = f"switch.smartgrade_{safe_name}_switch_{switch_num}"

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
        """Return the name of the switch."""
        device = self._get_device()
        device_name = device.get("name", "Unknown")
        
        # If device has multiple switches, add switch number
        switches = device.get("switches", {})
        if len(switches) > 1:
            return f"{device_name} Switch {self._switch_num}"
        else:
            # Single switch device - don't add number
            return device_name

    @property
    def is_on(self) -> bool:
        """Return True if switch is on."""
        device = self._get_device()
        switches = device.get("switches", {})
        return switches.get(f"switch_{self._switch_num}", False)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        device = self._get_device()
        # Device is available if online and coordinator has data
        return device.get("online", False) and self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device = self._get_device()
        return {
            "device_id": self._device_id,
            "site_name": device.get("site_name", ""),
            "mac_address": device.get("mac", ""),
            "online": device.get("online", False),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        _LOGGER.debug(
            "Turning on switch %d for device %s", self._switch_num, self._device_id
        )
        
        try:
            # Send toggle command to API
            switches = {f"switch_{self._switch_num}": True}
            await self.coordinator.api.async_toggle_device(self._device_id, switches)
            
            # Request immediate data refresh
            await self.coordinator.async_request_refresh()
            
        except Exception as err:
            _LOGGER.error(
                "Failed to turn on switch %d for device %s: %s",
                self._switch_num,
                self._device_id,
                err,
            )
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        _LOGGER.debug(
            "Turning off switch %d for device %s", self._switch_num, self._device_id
        )
        
        try:
            # Send toggle command to API
            switches = {f"switch_{self._switch_num}": False}
            await self.coordinator.api.async_toggle_device(self._device_id, switches)
            
            # Request immediate data refresh
            await self.coordinator.async_request_refresh()
            
        except Exception as err:
            _LOGGER.error(
                "Failed to turn off switch %d for device %s: %s",
                self._switch_num,
                self._device_id,
                err,
            )
            raise

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        device = self._get_device()
        device_type = device.get("type", "switch").lower()
        
        # Choose icon based on device type
        if "heater" in device_type or "boiler" in device_type:
            return "mdi:water-boiler" if self.is_on else "mdi:water-boiler-off"
        elif "outlet" in device_type or "socket" in device_type:
            return "mdi:power-socket" if self.is_on else "mdi:power-socket-off"
        else:
            return "mdi:toggle-switch" if self.is_on else "mdi:toggle-switch-off"
