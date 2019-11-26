"""
Sensor support for Ariston NET devices.
"""

DOMAIN='ariston'

from logging import getLogger
import voluptuous as vol

_LOGGER = getLogger(__name__)

from homeassistant.components.sensor import PLATFORM_SCHEMA

from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_NAME,
    TEMP_CELSIUS
)

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.exceptions import PlatformNotReady

from .AristonApi import (
    AristonApi,
    ATTR_ROOM_TEMPERATURE,
    ATTR_ROOM_TEMPERATURE_SET,
    ATTR_ACS_TEMPERATURE,
    ATTR_ACS_TEMPERATURE_SET,
    ATTR_HEAT_PUMP_ON,
    ATTR_EXTERNAL_TEMPERATURE,
    ATTR_LAST_UPDATE,
    CONF_DEVICE_ID
)

DEFAULT_NAME = 'Ariston NET'

SENSOR_TYPES = {
    ATTR_ROOM_TEMPERATURE: ['Room temperature', TEMP_CELSIUS, 'mdi:thermometer'],
    ATTR_ROOM_TEMPERATURE_SET: ['Room set', TEMP_CELSIUS, 'mdi:thermometer'],
    ATTR_ACS_TEMPERATURE: ['ACS temperature', TEMP_CELSIUS, 'mdi:thermometer'],
    ATTR_ACS_TEMPERATURE_SET: ['ACS set', TEMP_CELSIUS, 'mdi:thermometer'],
    ATTR_HEAT_PUMP_ON: ['Heat pump on?', 'booleano', 'mdi:snowflake'],
    ATTR_EXTERNAL_TEMPERATURE: ['External temperature', TEMP_CELSIUS, 'mdi:thermometer'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    name = config.get(CONF_NAME)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    device_id = config.get(CONF_DEVICE_ID)

    aristonApi = AristonApi(username=username, password=password, device_id=device_id)
    try:
        #Añadir tiempo para tener conexión, o validarlo en bucle
        aristonApi.update()
    except (ValueError, TypeError) as err:
        _LOGGER.error("Received error from Ariston: %s", err)
        
        if aristonApi.data is None:
            raise PlatformNotReady

    add_entities( [ AristonSensor(aristonApi, variable, name) for variable in SENSOR_TYPES], True)


class AristonSensor(Entity):
    """Representation of a sensor in the Ariston NET web."""

    def __init__(self, aristonApi, variable, name):
        """Initialize the sensor."""
        self._aristonApi = aristonApi
        self._variable = variable
        self._client_name = name

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self._client_name, self._variable)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._aristonApi.get_data(self._variable)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return SENSOR_TYPES[self._variable][1]

    @property
    def icon(self):
        """Return sensor specific icon."""
        return SENSOR_TYPES[self._variable][2]

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        return {
            ATTR_ROOM_TEMPERATURE: self._aristonApi.get_data(ATTR_ROOM_TEMPERATURE),
            ATTR_ROOM_TEMPERATURE_SET: self._aristonApi.get_data(ATTR_ROOM_TEMPERATURE_SET),
            ATTR_ACS_TEMPERATURE: self._aristonApi.get_data(ATTR_ACS_TEMPERATURE),
            ATTR_ACS_TEMPERATURE_SET: self._aristonApi.get_data(ATTR_ACS_TEMPERATURE_SET),
            ATTR_HEAT_PUMP_ON: self._aristonApi.get_data(ATTR_HEAT_PUMP_ON),
            ATTR_EXTERNAL_TEMPERATURE: self._aristonApi.get_data(ATTR_EXTERNAL_TEMPERATURE),
            CONF_DEVICE_ID: self._aristonApi.get_data(CONF_DEVICE_ID),
            ATTR_LAST_UPDATE: self._aristonApi.get_data(ATTR_LAST_UPDATE),
        }

    def update(self):
        """Delegate update to data class."""
        self._aristonApi.update()
