"""Token Manager for SmartGrade integration."""
import logging
import time
from typing import Any

import jwt

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .api_client import TokenExpiredError
from .const import (
    DOMAIN,
    ISSUE_TOKEN_EXPIRED,
    NOTIFICATION_TOKEN_EXPIRING,
    TOKEN_WARNING_DAYS,
)

_LOGGER = logging.getLogger(__name__)


class TokenManager:
    """Manage JWT token expiration and renewal.
    
    Monitors token expiration and triggers notifications/repair flows
    when token is expiring or has expired.
    """

    def __init__(self, hass: HomeAssistant, jwt_token: str):
        """Initialize token manager.
        
        Args:
            hass: Home Assistant instance
            jwt_token: JWT authentication token
        """
        self.hass = hass
        self.jwt_token = jwt_token
        self.user_id: int | None = None
        self.domain_id: int | None = None
        self.token_expiry: int | None = None
        self._warning_shown = False
        
        # Decode token to extract info
        try:
            decoded = jwt.decode(
                jwt_token, options={"verify_signature": False}
            )
            self.user_id = decoded.get("usr")
            self.domain_id = decoded.get("dom")
            self.token_expiry = decoded.get("exp")
            
            _LOGGER.debug(
                "Token info - User ID: %s, Domain ID: %s, Expiry: %s",
                self.user_id,
                self.domain_id,
                self.token_expiry,
            )
        except Exception as err:
            _LOGGER.error("Failed to decode JWT token: %s", err)

    async def check_expiration(self) -> None:
        """Check if token is expired or expiring soon.
        
        Raises:
            TokenExpiredError: If token has expired
        """
        if not self.token_expiry:
            _LOGGER.warning("Token expiry not available, cannot check expiration")
            return
        
        now = int(time.time())
        seconds_remaining = self.token_expiry - now
        
        # Token expired
        if seconds_remaining <= 0:
            _LOGGER.error("JWT token has expired")
            await self.trigger_repair_flow()
            raise TokenExpiredError("JWT token has expired")
        
        # Token expiring soon (within warning period)
        days_remaining = seconds_remaining / 86400
        if days_remaining <= TOKEN_WARNING_DAYS and not self._warning_shown:
            _LOGGER.warning(
                "JWT token expiring in %.1f days (%d seconds)",
                days_remaining,
                seconds_remaining,
            )
            await self._create_expiry_notification(seconds_remaining)
            self._warning_shown = True
        
        _LOGGER.debug(
            "Token valid for %.1f more days (%d seconds)",
            days_remaining,
            seconds_remaining,
        )

    async def _create_expiry_notification(self, seconds_remaining: int) -> None:
        """Create persistent notification about token expiry.
        
        Args:
            seconds_remaining: Seconds until token expires
        """
        days = int(seconds_remaining / 86400)
        hours = int((seconds_remaining % 86400) / 3600)
        
        message = (
            f"Your SmartGrade authentication token expires in {days} day(s) "
            f"and {hours} hour(s).\n\n"
            "Please reconfigure the integration to re-authenticate via SMS "
            "before the token expires to avoid service interruption."
        )
        
        try:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "SmartGrade Token Expiring Soon",
                    "message": message,
                    "notification_id": NOTIFICATION_TOKEN_EXPIRING,
                },
                blocking=True,
            )
            _LOGGER.info("Created token expiry notification (days remaining: %d)", days)
        except Exception as err:
            _LOGGER.error("Failed to create expiry notification: %s", err)

    async def trigger_repair_flow(self) -> None:
        """Trigger Home Assistant repair flow for re-authentication."""
        try:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                ISSUE_TOKEN_EXPIRED,
                is_fixable=True,
                severity=ir.IssueSeverity.ERROR,
                translation_key="token_expired",
                translation_placeholders={
                    "days": str(TOKEN_WARNING_DAYS),
                },
            )
            _LOGGER.info("Created repair issue for token expiration")
        except Exception as err:
            _LOGGER.error("Failed to create repair issue: %s", err)

    def get_token_info(self) -> dict[str, Any]:
        """Get token information.
        
        Returns:
            Dictionary with user_id, domain_id, and expiry information
        """
        if not self.token_expiry:
            return {}
        
        now = int(time.time())
        seconds_remaining = self.token_expiry - now
        
        return {
            "user_id": self.user_id,
            "domain_id": self.domain_id,
            "expiry_timestamp": self.token_expiry,
            "seconds_remaining": seconds_remaining,
            "days_remaining": seconds_remaining / 86400,
            "is_expired": seconds_remaining <= 0,
            "is_expiring_soon": seconds_remaining <= (TOKEN_WARNING_DAYS * 86400),
        }

    @property
    def is_expired(self) -> bool:
        """Return True if token is expired."""
        if not self.token_expiry:
            return True
        return int(time.time()) >= self.token_expiry

    @property
    def is_expiring_soon(self) -> bool:
        """Return True if token is expiring within warning period."""
        if not self.token_expiry:
            return True
        now = int(time.time())
        return (self.token_expiry - now) <= (TOKEN_WARNING_DAYS * 86400)
