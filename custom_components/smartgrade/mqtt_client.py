"""MQTT Client for SmartGrade real-time device updates."""
import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt

from .const import (
    MQTT_BROKER,
    MQTT_KEEPALIVE,
    MQTT_PORT,
    MQTT_TOPIC_SUBSCRIBE_ALL_POWER,
    MQTT_TOPIC_SUBSCRIBE_ALL_SENSOR,
)

_LOGGER = logging.getLogger(__name__)


class SmartGradeMQTTClient:
    """MQTT Client for real-time device state updates.
    
    Connects to SmartGrade MQTT broker to receive instant device state changes.
    Falls back gracefully if MQTT is unavailable.
    """

    def __init__(
        self,
        user_id: int,
        domain_id: int,
        jwt_token: str,
        on_message_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ):
        """Initialize MQTT client.
        
        Args:
            user_id: User ID from JWT token (used as MQTT username)
            domain_id: Domain ID from JWT token (used in topics)
            jwt_token: JWT token (used as MQTT password)
            on_message_callback: Callback function for received messages
        """
        self.user_id = user_id
        self.domain_id = domain_id
        self.jwt_token = jwt_token
        self.on_message_callback = on_message_callback
        
        self.client: mqtt.Client | None = None
        self.connected = False
        self._reconnect_task: asyncio.Task | None = None
        self._reconnect_delay = 5  # seconds
        self._max_reconnect_delay = 300  # 5 minutes

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            self.connected = True
            _LOGGER.info("Connected to SmartGrade MQTT broker")
            
            # Subscribe to device state topics
            power_topic = MQTT_TOPIC_SUBSCRIBE_ALL_POWER.format(
                domain_id=self.domain_id
            )
            sensor_topic = MQTT_TOPIC_SUBSCRIBE_ALL_SENSOR.format(
                domain_id=self.domain_id
            )
            
            client.subscribe(power_topic)
            client.subscribe(sensor_topic)
            _LOGGER.debug(
                "Subscribed to MQTT topics: %s, %s", power_topic, sensor_topic
            )
            
            # Reset reconnect delay on successful connection
            self._reconnect_delay = 5
        else:
            self.connected = False
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized",
            }
            error_msg = error_messages.get(rc, f"Connection refused - code {rc}")
            _LOGGER.error("MQTT connection failed: %s", error_msg)

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        self.connected = False
        if rc != 0:
            _LOGGER.warning(
                "Unexpected MQTT disconnection (code %d), will attempt to reconnect",
                rc,
            )

    def _on_message(self, client, userdata, msg):
        """Callback when a message is received."""
        try:
            # Parse topic to extract device ID
            # Topic format: s/{domain_id}/{device_id}/power or /sensor
            topic_parts = msg.topic.split("/")
            if len(topic_parts) < 4:
                _LOGGER.warning("Invalid MQTT topic format: %s", msg.topic)
                return
            
            device_id = topic_parts[2]
            message_type = topic_parts[3]  # 'power' or 'sensor'
            
            # Parse JSON payload
            try:
                payload = json.loads(msg.payload.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as err:
                _LOGGER.warning(
                    "Failed to decode MQTT message from %s: %s", msg.topic, err
                )
                return
            
            _LOGGER.debug(
                "Received MQTT message - device: %s, type: %s, payload: %s",
                device_id,
                message_type,
                payload,
            )
            
            # Call the callback if registered
            if self.on_message_callback:
                self.on_message_callback(device_id, message_type, payload)
                
        except Exception as err:
            _LOGGER.exception("Error processing MQTT message: %s", err)

    async def async_connect(self) -> bool:
        """Connect to MQTT broker.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # Create MQTT client
            client_id = f"ha_smartgrade_{self.user_id}_{id(self)}"
            self.client = mqtt.Client(client_id=client_id)
            
            # Set credentials: username = user_id, password = JWT token
            self.client.username_pw_set(str(self.user_id), self.jwt_token)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Connect to broker
            _LOGGER.info(
                "Connecting to MQTT broker %s:%d as user %s",
                MQTT_BROKER,
                MQTT_PORT,
                self.user_id,
            )
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.connect(
                    MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE
                ),
            )
            
            # Start network loop in background
            self.client.loop_start()
            
            # Wait a bit for connection to establish
            await asyncio.sleep(2)
            
            if self.connected:
                _LOGGER.info("Successfully connected to MQTT broker")
                return True
            else:
                _LOGGER.warning("MQTT connection timeout")
                return False
                
        except Exception as err:
            _LOGGER.error("Failed to connect to MQTT broker: %s", err)
            self.connected = False
            return False

    async def async_disconnect(self):
        """Disconnect from MQTT broker."""
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None
        
        if self.client:
            self.client.loop_stop()
            await asyncio.get_event_loop().run_in_executor(
                None, self.client.disconnect
            )
            self.client = None
        
        self.connected = False
        _LOGGER.info("Disconnected from MQTT broker")

    def register_callback(
        self, callback: Callable[[str, str, dict[str, Any]], None]
    ):
        """Register callback for received messages.
        
        Args:
            callback: Function to call with (device_id, message_type, payload)
        """
        self.on_message_callback = callback
        _LOGGER.debug("Registered MQTT message callback")

    @property
    def is_connected(self) -> bool:
        """Return True if connected to MQTT broker."""
        return self.connected
