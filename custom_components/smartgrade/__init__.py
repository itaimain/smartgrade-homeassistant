"""The SmartGrade integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api_client import SmartGradeAPIClient, TokenExpiredError
from .const import (
    CONF_DOMAIN_ID,
    CONF_JWT_TOKEN,
    CONF_USER_ID,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import SmartGradeDataUpdateCoordinator
from .mqtt_client import SmartGradeMQTTClient
from .token_manager import TokenManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SmartGrade from a config entry."""
    _LOGGER.debug("Setting up SmartGrade integration")
    
    # Extract configuration
    jwt_token = entry.data[CONF_JWT_TOKEN]
    user_id = entry.data[CONF_USER_ID]
    domain_id = entry.data[CONF_DOMAIN_ID]
    
    # Initialize token manager
    token_mgr = TokenManager(hass, jwt_token)
    
    # Check token expiration on startup
    try:
        await token_mgr.check_expiration()
    except TokenExpiredError as err:
        _LOGGER.error("Token expired on startup: %s", err)
        # Trigger re-auth flow
        raise ConfigEntryAuthFailed("JWT token has expired") from err
    
    # Initialize API client
    session = async_get_clientsession(hass)
    api = SmartGradeAPIClient(session, jwt_token, user_id, domain_id)
    
    # Test API connectivity
    try:
        devices = await api.async_get_devices()
        _LOGGER.info("Successfully connected to SmartGrade API, found %d devices", len(devices))
    except TokenExpiredError as err:
        _LOGGER.error("Token expired during initial device fetch: %s", err)
        raise ConfigEntryAuthFailed("JWT token has expired") from err
    except Exception as err:
        _LOGGER.error("Failed to connect to SmartGrade API: %s", err)
        raise ConfigEntryNotReady(f"Failed to connect: {err}") from err
    
    # Initialize MQTT client (optional, graceful fallback)
    mqtt_client = None
    try:
        mqtt_client = SmartGradeMQTTClient(user_id, domain_id, jwt_token)
        connected = await mqtt_client.async_connect()
        if connected:
            _LOGGER.info("MQTT connected - real-time updates enabled")
        else:
            _LOGGER.warning("MQTT connection failed - using HTTP polling only")
            mqtt_client = None
    except Exception as err:
        _LOGGER.warning("Failed to initialize MQTT client: %s - using HTTP polling only", err)
        mqtt_client = None
    
    # Initialize data update coordinator
    coordinator = SmartGradeDataUpdateCoordinator(hass, api, mqtt_client, token_mgr)
    
    # Fetch initial data
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        # Token expired during first refresh
        raise
    except Exception as err:
        _LOGGER.error("Failed to fetch initial data: %s", err)
        raise ConfigEntryNotReady(f"Failed to fetch data: {err}") from err
    
    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    await async_setup_services(hass, entry)
    
    _LOGGER.info("SmartGrade integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading SmartGrade integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Cleanup coordinator
        coordinator: SmartGradeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_shutdown()
        
        # Remove from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)
    
    _LOGGER.info("SmartGrade integration unloaded")
    return unload_ok


async def async_setup_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up services for SmartGrade integration."""
    import voluptuous as vol
    from homeassistant.helpers import config_validation as cv
    
    coordinator: SmartGradeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async def handle_create_timer(call):
        """Handle create_timer service call."""
        device_id = call.data.get("device_id")
        time_str = call.data.get("time")
        action = call.data.get("action")
        days = call.data.get("days", [])
        
        # Convert entity_id to device_id if needed
        if device_id and device_id.startswith("switch."):
            # Extract device_id from entity
            for dev_id, device in coordinator.data.items():
                if device_id.endswith(dev_id.lower().replace(" ", "_")):
                    device_id = dev_id
                    break
        
        timer_data = {
            "time": time_str,
            "action": action,
            "days": days,
        }
        
        try:
            await coordinator.api.async_create_timer(device_id, timer_data)
            await coordinator.async_request_refresh()
            _LOGGER.info("Created timer for device %s", device_id)
        except Exception as err:
            _LOGGER.error("Failed to create timer: %s", err)
            raise
    
    async def handle_delete_timer(call):
        """Handle delete_timer service call."""
        device_id = call.data.get("device_id")
        timer_id = call.data.get("timer_id")
        
        # Convert entity_id to device_id if needed
        if device_id and device_id.startswith("switch."):
            # Extract device_id from entity
            for dev_id, device in coordinator.data.items():
                if device_id.endswith(dev_id.lower().replace(" ", "_")):
                    device_id = dev_id
                    break
        
        try:
            await coordinator.api.async_delete_timer(device_id, timer_id)
            await coordinator.async_request_refresh()
            _LOGGER.info("Deleted timer %s from device %s", timer_id, device_id)
        except Exception as err:
            _LOGGER.error("Failed to delete timer: %s", err)
            raise
    
    # Register services only once (check if already registered)
    if not hass.services.has_service(DOMAIN, "create_timer"):
        hass.services.async_register(
            DOMAIN,
            "create_timer",
            handle_create_timer,
            schema=vol.Schema(
                {
                    vol.Required("device_id"): cv.string,
                    vol.Required("time"): cv.string,
                    vol.Required("action"): vol.In(["on", "off"]),
                    vol.Optional("days", default=[]): cv.ensure_list,
                }
            ),
        )
        _LOGGER.debug("Registered create_timer service")
    
    if not hass.services.has_service(DOMAIN, "delete_timer"):
        hass.services.async_register(
            DOMAIN,
            "delete_timer",
            handle_delete_timer,
            schema=vol.Schema(
                {
                    vol.Required("device_id"): cv.string,
                    vol.Required("timer_id"): cv.string,
                }
            ),
        )
        _LOGGER.debug("Registered delete_timer service")
