"""SmartGrade API Client for Home Assistant."""
import asyncio
import base64
import logging
from typing import Any, Optional

import aiohttp
from aiohttp import ClientError, ClientTimeout

from .const import (
    API_APPS_TOKEN,
    API_BASE_URL,
    API_CUSTOMERS,
    API_DEVICE_KWH,
    API_DEVICE_TIMERS,
    API_DEVICE_TIMER,
    API_DEVICE_TOGGLE,
    API_DEVICES,
    API_LOGIN_CODE,
    API_SITE_DEVICES,
    API_TIMEOUT,
    API_USER,
    API_USER_PROFILE,
    API_USER_SITES,
    BASIC_AUTH_PASS,
    BASIC_AUTH_USER,
    ERROR_AUTH_FAILED,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_CODE,
    ERROR_TOKEN_EXPIRED,
    ERROR_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class SmartGradeAuthError(Exception):
    """Custom exception for SmartGrade authentication errors."""


class TokenExpiredError(SmartGradeAuthError):
    """Exception raised when JWT token has expired."""


class InvalidCodeError(SmartGradeAuthError):
    """Exception raised when SMS code is invalid."""


class SmartGradeAPIClient:
    """SmartGrade API Client for Home Assistant.
    
    Handles all HTTP API interactions with SmartGrade backend including:
    - Authentication (app token, SMS request/verify)
    - Device management (list, control, timers)
    - Energy monitoring
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        jwt_token: Optional[str] = None,
        user_id: Optional[int] = None,
        domain_id: Optional[int] = None,
    ):
        """Initialize the API client.
        
        Args:
            session: aiohttp ClientSession for making requests
            jwt_token: JWT authentication token (if already authenticated)
            user_id: User ID from JWT token
            domain_id: Domain ID from JWT token
        """
        self.session = session
        self.base_url = API_BASE_URL
        self.jwt_token = jwt_token
        self.user_id = user_id
        self.domain_id = domain_id
        self._app_token: Optional[str] = None

    async def _get_app_token(self) -> str:
        """Get App Token using Basic Authentication.
        
        Returns:
            App token string
            
        Raises:
            SmartGradeAuthError: If token retrieval fails
        """
        if self._app_token:
            return self._app_token

        # Create Basic Auth header
        credentials = f"{BASIC_AUTH_USER}:{BASIC_AUTH_PASS}"
        basic_auth = base64.b64encode(credentials.encode()).decode()

        headers = {"Authorization": f"Basic {basic_auth}"}

        try:
            async with self.session.get(
                f"{self.base_url}{API_APPS_TOKEN}",
                headers=headers,
                timeout=ClientTimeout(total=API_TIMEOUT),
            ) as response:
                response.raise_for_status()
                data = await response.json()
                self._app_token = data.get("token")

                if not self._app_token:
                    raise SmartGradeAuthError("No token in response")

                _LOGGER.debug("Successfully obtained app token")
                return self._app_token

        except asyncio.TimeoutError as err:
            raise SmartGradeAuthError(f"Timeout getting app token: {err}") from err
        except ClientError as err:
            raise SmartGradeAuthError(f"Failed to get app token: {err}") from err

    async def async_request_sms(self, phone_number: str) -> dict[str, Any]:
        """Request SMS verification code for a phone number.
        
        Args:
            phone_number: Israeli phone number (e.g., "0501234567")
            
        Returns:
            Response data including user ID and formatted mobile number
            
        Raises:
            SmartGradeAuthError: If SMS request fails
        """
        # Get app token first
        app_token = await self._get_app_token()

        # Prepare payload - APK uses nested structure
        payload = {"customer": {"mobile": phone_number}}

        # Use X-APP-TOKEN header (not Authorization!)
        headers = {"X-APP-TOKEN": f"Bearer {app_token}"}

        try:
            async with self.session.post(
                f"{self.base_url}{API_CUSTOMERS}",
                json=payload,
                headers=headers,
                timeout=ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 409:
                    # Customer already exists - this is OK, SMS may still be sent
                    _LOGGER.info("Customer already registered, SMS code sent")
                    return {"success": True, "message": "Customer already registered"}

                response.raise_for_status()
                data = await response.json()
                _LOGGER.info("SMS verification code sent to %s", phone_number)
                return data

        except asyncio.TimeoutError as err:
            raise SmartGradeAuthError(f"Timeout requesting SMS: {err}") from err
        except ClientError as err:
            raise SmartGradeAuthError(f"Failed to request SMS: {err}") from err

    async def async_verify_sms(self, sms_code: str) -> str:
        """Verify SMS code and obtain JWT token.
        
        Args:
            sms_code: 6-digit SMS verification code
            
        Returns:
            JWT token string
            
        Raises:
            InvalidCodeError: If SMS code is invalid
            SmartGradeAuthError: If verification fails
        """
        # Get app token first
        app_token = await self._get_app_token()

        # Prepare payload - APK uses nested structure
        payload = {"user": {"code": sms_code}}

        # Use X-APP-TOKEN header (not Authorization!)
        headers = {"X-APP-TOKEN": f"Bearer {app_token}"}

        try:
            async with self.session.post(
                f"{self.base_url}{API_LOGIN_CODE}",
                json=payload,
                headers=headers,
                timeout=ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 400:
                    raise InvalidCodeError("Invalid SMS code")

                response.raise_for_status()
                data = await response.json()

                # API returns token in "jwt" field, not "id_token"
                self.jwt_token = data.get("jwt") or data.get("id_token")

                if not self.jwt_token:
                    raise SmartGradeAuthError("No JWT token in response")

                _LOGGER.info("Successfully authenticated with SMS code")
                return self.jwt_token

        except InvalidCodeError:
            raise
        except asyncio.TimeoutError as err:
            raise SmartGradeAuthError(f"Timeout verifying SMS: {err}") from err
        except ClientError as err:
            raise SmartGradeAuthError(f"Failed to verify SMS code: {err}") from err

    async def async_get_user_info(self) -> dict[str, Any]:
        """Get current user information.
        
        Returns:
            User data including ID, domain, etc.
            
        Raises:
            TokenExpiredError: If JWT token has expired
            SmartGradeAuthError: If request fails
        """
        if not self.jwt_token:
            raise SmartGradeAuthError("Not authenticated - no JWT token")

        headers = {"Authorization": f"Bearer {self.jwt_token}"}

        try:
            async with self.session.get(
                f"{self.base_url}{API_USER}",
                headers=headers,
                timeout=ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise TokenExpiredError("JWT token has expired")

                response.raise_for_status()
                return await response.json()

        except TokenExpiredError:
            raise
        except asyncio.TimeoutError as err:
            raise SmartGradeAuthError(f"Timeout getting user info: {err}") from err
        except ClientError as err:
            raise SmartGradeAuthError(f"Failed to get user info: {err}") from err

    async def async_get_sites(self, with_shared: bool = True) -> list[dict[str, Any]]:
        """Get all sites (locations) for the user.
        
        Args:
            with_shared: Include shared sites
            
        Returns:
            List of site data
            
        Raises:
            TokenExpiredError: If JWT token has expired
            SmartGradeAuthError: If request fails
        """
        if not self.jwt_token or not self.user_id:
            raise SmartGradeAuthError("Not authenticated - no JWT token or user ID")

        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        params = {"shared": str(with_shared).lower()}
        url = f"{self.base_url}{API_USER_SITES}".format(user_id=self.user_id)

        try:
            async with self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise TokenExpiredError("JWT token has expired")

                response.raise_for_status()
                data = await response.json()
                # API returns list directly, not wrapped in dict
                if isinstance(data, list):
                    return data
                return data.get("sites", [])

        except TokenExpiredError:
            raise
        except asyncio.TimeoutError as err:
            raise SmartGradeAuthError(f"Timeout getting sites: {err}") from err
        except ClientError as err:
            raise SmartGradeAuthError(f"Failed to get sites: {err}") from err

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Get all devices across all sites.
        
        Returns:
            List of device data
            
        Raises:
            TokenExpiredError: If JWT token has expired
            SmartGradeAuthError: If request fails
        """
        # Get all sites first
        sites = await self.async_get_sites()

        # Collect devices from all sites
        all_devices = []
        for site in sites:
            site_id = site.get("id")
            if site_id:
                devices = await self.async_get_site_devices(site_id)
                # Add site info to each device
                for device in devices:
                    device["site_id"] = site_id
                    device["site_name"] = site.get("name", "Unknown")
                all_devices.extend(devices)

        _LOGGER.debug("Found %d devices across %d sites", len(all_devices), len(sites))
        return all_devices

    async def async_get_site_devices(self, site_id: str) -> list[dict[str, Any]]:
        """Get all devices for a specific site.
        
        Args:
            site_id: Site ID
            
        Returns:
            List of device data
            
        Raises:
            TokenExpiredError: If JWT token has expired
            SmartGradeAuthError: If request fails
        """
        if not self.jwt_token:
            raise SmartGradeAuthError("Not authenticated - no JWT token")

        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        url = f"{self.base_url}{API_SITE_DEVICES}".format(site_id=site_id)

        try:
            async with self.session.get(
                url, headers=headers, timeout=ClientTimeout(total=API_TIMEOUT)
            ) as response:
                if response.status == 401:
                    raise TokenExpiredError("JWT token has expired")

                response.raise_for_status()
                data = await response.json()
                # API may return list directly or wrapped in dict
                if isinstance(data, list):
                    return data
                return data.get("devices", [])

        except TokenExpiredError:
            raise
        except asyncio.TimeoutError as err:
            raise SmartGradeAuthError(f"Timeout getting devices: {err}") from err
        except ClientError as err:
            raise SmartGradeAuthError(f"Failed to get devices: {err}") from err

    async def async_toggle_device(
        self, device_id: str, switches: dict[str, bool]
    ) -> dict[str, Any]:
        """Toggle device switches (on/off control).
        
        Args:
            device_id: Device ID
            switches: Dictionary of switch states (e.g., {"switch_1": True})
            
        Returns:
            Device state response
            
        Raises:
            TokenExpiredError: If JWT token has expired
            SmartGradeAuthError: If request fails
        """
        if not self.jwt_token:
            raise SmartGradeAuthError("Not authenticated - no JWT token")

        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        url = f"{self.base_url}{API_DEVICE_TOGGLE}".format(device_id=device_id)

        try:
            async with self.session.post(
                url,
                json=switches,
                headers=headers,
                timeout=ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise TokenExpiredError("JWT token has expired")

                response.raise_for_status()
                data = await response.json()
                _LOGGER.debug(
                    "Toggled device %s switches: %s", device_id, switches
                )
                return data

        except TokenExpiredError:
            raise
        except asyncio.TimeoutError as err:
            raise SmartGradeAuthError(f"Timeout toggling device: {err}") from err
        except ClientError as err:
            raise SmartGradeAuthError(f"Failed to toggle device: {err}") from err

    async def async_get_device_timers(self, device_id: str) -> list[dict[str, Any]]:
        """Get all timers for a device.
        
        Args:
            device_id: Device ID
            
        Returns:
            List of timer data
            
        Raises:
            TokenExpiredError: If JWT token has expired
            SmartGradeAuthError: If request fails
        """
        if not self.jwt_token:
            raise SmartGradeAuthError("Not authenticated - no JWT token")

        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        url = f"{self.base_url}{API_DEVICE_TIMERS}".format(device_id=device_id)

        try:
            async with self.session.get(
                url, headers=headers, timeout=ClientTimeout(total=API_TIMEOUT)
            ) as response:
                if response.status == 401:
                    raise TokenExpiredError("JWT token has expired")

                response.raise_for_status()
                data = await response.json()
                return data.get("timers", [])

        except TokenExpiredError:
            raise
        except asyncio.TimeoutError as err:
            raise SmartGradeAuthError(f"Timeout getting timers: {err}") from err
        except ClientError as err:
            raise SmartGradeAuthError(f"Failed to get timers: {err}") from err

    async def async_create_timer(
        self, device_id: str, timer_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new timer for a device.
        
        Args:
            device_id: Device ID
            timer_data: Timer configuration
            
        Returns:
            Created timer data
            
        Raises:
            TokenExpiredError: If JWT token has expired
            SmartGradeAuthError: If request fails
        """
        if not self.jwt_token:
            raise SmartGradeAuthError("Not authenticated - no JWT token")

        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        url = f"{self.base_url}{API_DEVICE_TIMERS}".format(device_id=device_id)

        try:
            async with self.session.post(
                url,
                json=timer_data,
                headers=headers,
                timeout=ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise TokenExpiredError("JWT token has expired")

                response.raise_for_status()
                _LOGGER.info("Created timer for device %s", device_id)
                return await response.json()

        except TokenExpiredError:
            raise
        except asyncio.TimeoutError as err:
            raise SmartGradeAuthError(f"Timeout creating timer: {err}") from err
        except ClientError as err:
            raise SmartGradeAuthError(f"Failed to create timer: {err}") from err

    async def async_delete_timer(self, device_id: str, timer_id: str) -> None:
        """Delete a timer from a device.
        
        Args:
            device_id: Device ID
            timer_id: Timer ID to delete
            
        Raises:
            TokenExpiredError: If JWT token has expired
            SmartGradeAuthError: If request fails
        """
        if not self.jwt_token:
            raise SmartGradeAuthError("Not authenticated - no JWT token")

        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        url = f"{self.base_url}{API_DEVICE_TIMER}".format(
            device_id=device_id, timer_id=timer_id
        )

        try:
            async with self.session.delete(
                url, headers=headers, timeout=ClientTimeout(total=API_TIMEOUT)
            ) as response:
                if response.status == 401:
                    raise TokenExpiredError("JWT token has expired")

                response.raise_for_status()
                _LOGGER.info("Deleted timer %s from device %s", timer_id, device_id)

        except TokenExpiredError:
            raise
        except asyncio.TimeoutError as err:
            raise SmartGradeAuthError(f"Timeout deleting timer: {err}") from err
        except ClientError as err:
            raise SmartGradeAuthError(f"Failed to delete timer: {err}") from err

    async def async_get_device_kwh(
        self, device_id: str, start_timestamp: int, end_timestamp: int, timezone: int = 2
    ) -> dict[str, Any]:
        """Get energy consumption (kWh) for a device.
        
        Args:
            device_id: Device ID
            start_timestamp: Start time (Unix timestamp in seconds)
            end_timestamp: End time (Unix timestamp in seconds)
            timezone: Timezone offset (default: +2 for Israel)
            
        Returns:
            Energy consumption data
            
        Raises:
            TokenExpiredError: If JWT token has expired
            SmartGradeAuthError: If request fails
        """
        if not self.jwt_token:
            raise SmartGradeAuthError("Not authenticated - no JWT token")

        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        url = f"{self.base_url}{API_DEVICE_KWH}".format(device_id=device_id)
        params = {
            "startTimestampSeconds": start_timestamp,
            "endTimestampSeconds": end_timestamp,
            "timeZone": timezone,
        }

        try:
            async with self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise TokenExpiredError("JWT token has expired")

                response.raise_for_status()
                return await response.json()

        except TokenExpiredError:
            raise
        except asyncio.TimeoutError as err:
            raise SmartGradeAuthError(f"Timeout getting kWh data: {err}") from err
        except ClientError as err:
            raise SmartGradeAuthError(f"Failed to get kWh data: {err}") from err
