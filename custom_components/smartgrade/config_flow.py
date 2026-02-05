"""Config flow for SmartGrade integration."""
import logging
from typing import Any

import jwt
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api_client import (
    InvalidCodeError,
    SmartGradeAPIClient,
    SmartGradeAuthError,
)
from .const import (
    CONF_DOMAIN_ID,
    CONF_JWT_TOKEN,
    CONF_PHONE_NUMBER,
    CONF_TOKEN_EXPIRY,
    CONF_USER_ID,
    DOMAIN,
    ERROR_AUTH_FAILED,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_CODE,
    ERROR_TIMEOUT,
    ERROR_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


class SmartGradeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartGrade."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._phone_number: str | None = None
        self._reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - phone number entry."""
        errors = {}

        if user_input is not None:
            self._phone_number = user_input[CONF_PHONE_NUMBER]
            
            # Request SMS code
            session = async_get_clientsession(self.hass)
            api = SmartGradeAPIClient(session)
            
            try:
                await api.async_request_sms(self._phone_number)
                _LOGGER.info("SMS code requested for %s", self._phone_number)
                return await self.async_step_sms()
            
            except SmartGradeAuthError as err:
                _LOGGER.error("Failed to request SMS: %s", err)
                if "timeout" in str(err).lower():
                    errors["base"] = ERROR_TIMEOUT
                else:
                    errors["base"] = ERROR_CANNOT_CONNECT

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PHONE_NUMBER,
                        default=self._phone_number or "",
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "example": "0501234567",
            },
        )

    async def async_step_sms(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle SMS code verification step."""
        errors = {}

        if user_input is not None:
            sms_code = user_input.get("sms_code", "").strip()
            
            if not sms_code:
                errors["base"] = ERROR_INVALID_CODE
            else:
                session = async_get_clientsession(self.hass)
                api = SmartGradeAPIClient(session)
                
                try:
                    # Verify SMS code and get JWT token
                    jwt_token = await api.async_verify_sms(sms_code)
                    
                    # Decode JWT to extract user/domain IDs
                    decoded = jwt.decode(
                        jwt_token, options={"verify_signature": False}
                    )
                    user_id = decoded.get("usr")
                    domain_id = decoded.get("dom")
                    token_expiry = decoded.get("exp")
                    
                    _LOGGER.info(
                        "Successfully authenticated for %s (user_id: %s, domain_id: %s)",
                        self._phone_number,
                        user_id,
                        domain_id,
                    )
                    
                    # Check if this is a reauth flow
                    if self._reauth_entry:
                        # Update existing entry
                        self.hass.config_entries.async_update_entry(
                            self._reauth_entry,
                            data={
                                CONF_PHONE_NUMBER: self._phone_number,
                                CONF_JWT_TOKEN: jwt_token,
                                CONF_USER_ID: user_id,
                                CONF_DOMAIN_ID: domain_id,
                                CONF_TOKEN_EXPIRY: token_expiry,
                            },
                        )
                        await self.hass.config_entries.async_reload(
                            self._reauth_entry.entry_id
                        )
                        return self.async_abort(reason="reauth_successful")
                    
                    # Create new entry
                    await self.async_set_unique_id(str(user_id))
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=f"SmartGrade ({self._phone_number})",
                        data={
                            CONF_PHONE_NUMBER: self._phone_number,
                            CONF_JWT_TOKEN: jwt_token,
                            CONF_USER_ID: user_id,
                            CONF_DOMAIN_ID: domain_id,
                            CONF_TOKEN_EXPIRY: token_expiry,
                        },
                    )
                
                except InvalidCodeError:
                    _LOGGER.warning("Invalid SMS code entered")
                    errors["base"] = ERROR_INVALID_CODE
                
                except SmartGradeAuthError as err:
                    _LOGGER.error("Authentication failed: %s", err)
                    if "timeout" in str(err).lower():
                        errors["base"] = ERROR_TIMEOUT
                    else:
                        errors["base"] = ERROR_AUTH_FAILED
                
                except Exception as err:
                    _LOGGER.exception("Unexpected error during authentication: %s", err)
                    errors["base"] = ERROR_UNKNOWN

        return self.async_show_form(
            step_id="sms",
            data_schema=vol.Schema(
                {
                    vol.Required("sms_code"): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "phone_number": self._phone_number or "",
            },
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle re-authentication when token expires."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        
        # Pre-fill phone number from existing entry
        if self._reauth_entry:
            self._phone_number = self._reauth_entry.data.get(CONF_PHONE_NUMBER)
        
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm re-authentication."""
        errors = {}

        if user_input is not None:
            # Request new SMS code
            session = async_get_clientsession(self.hass)
            api = SmartGradeAPIClient(session)
            
            try:
                await api.async_request_sms(self._phone_number)
                _LOGGER.info("SMS code requested for re-auth: %s", self._phone_number)
                return await self.async_step_sms()
            
            except SmartGradeAuthError as err:
                _LOGGER.error("Failed to request SMS for re-auth: %s", err)
                if "timeout" in str(err).lower():
                    errors["base"] = ERROR_TIMEOUT
                else:
                    errors["base"] = ERROR_CANNOT_CONNECT

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={
                "phone_number": self._phone_number or "",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return SmartGradeOptionsFlowHandler(config_entry)


class SmartGradeOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for SmartGrade."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Currently no options to configure
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )
