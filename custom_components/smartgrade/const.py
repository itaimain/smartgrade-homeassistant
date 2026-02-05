"""Constants for the SmartGrade integration."""

DOMAIN = "smartgrade"

# Configuration keys
CONF_PHONE_NUMBER = "phone_number"
CONF_JWT_TOKEN = "jwt_token"
CONF_USER_ID = "user_id"
CONF_DOMAIN_ID = "domain_id"
CONF_TOKEN_EXPIRY = "token_expiry"

# API Configuration
API_BASE_URL = "https://api.iotechv.com"
API_TIMEOUT = 10

# From APK reverse engineering - Basic Auth credentials for app token
BASIC_AUTH_USER = "dealor_app"
BASIC_AUTH_PASS = "J2AQHSrNXMkuv70UDh2F"

# MQTT Configuration
MQTT_BROKER = "63.32.36.56"  # vernemq.iotechv.com
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

# Update intervals
SCAN_INTERVAL = 10  # seconds (HTTP polling for state updates)
SCAN_INTERVAL_MQTT = 60  # seconds (when MQTT connected, only for timers/schedules)
TOKEN_WARNING_DAYS = 3

# Platforms
PLATFORMS = ["switch", "sensor"]

# API Endpoints
API_APPS_TOKEN = "/api/v1/apps/token"
API_CUSTOMERS = "/api/v1/customers"
API_LOGIN_CODE = "/api/v1/users/login/code"
API_USER = "/api/v1/users"
API_DEVICES = "/api/v1/devices"
API_DEVICE_TOGGLE = "/api/v1/devices/{device_id}/toggle_switches"
API_DEVICE_TIMERS = "/api/v1/devices/{device_id}/timers"
API_DEVICE_TIMER = "/api/v1/devices/{device_id}/timers/{timer_id}"
API_DEVICE_KWH = "/api/v1/devices/{device_id}/kwh"
API_USER_SITES = "/api/v1/users/{user_id}/sites"
API_SITE_DEVICES = "/api/v1/sites/{site_id}/devices"
API_USER_PROFILE = "/api/v1/users/profile"

# MQTT Topics
MQTT_TOPIC_POWER = "s/{domain_id}/{device_id}/power"
MQTT_TOPIC_SENSOR = "s/{domain_id}/{device_id}/sensor"
MQTT_TOPIC_SUBSCRIBE_ALL_POWER = "s/{domain_id}/+/power"
MQTT_TOPIC_SUBSCRIBE_ALL_SENSOR = "s/{domain_id}/+/sensor"

# Error messages
ERROR_AUTH_FAILED = "authentication_failed"
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_INVALID_CODE = "invalid_code"
ERROR_TOKEN_EXPIRED = "token_expired"
ERROR_TIMEOUT = "timeout"
ERROR_UNKNOWN = "unknown"

# Notification IDs
NOTIFICATION_TOKEN_EXPIRING = "smartgrade_token_expiring"
NOTIFICATION_TOKEN_EXPIRED = "smartgrade_token_expired"

# Issue IDs for repairs
ISSUE_TOKEN_EXPIRED = "token_expired"
