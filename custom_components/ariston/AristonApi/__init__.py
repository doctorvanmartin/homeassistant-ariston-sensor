import requests
from datetime import timedelta, datetime
from logging import getLogger
from homeassistant.util import Throttle

_LOGGER = getLogger(__name__)

from homeassistant.components.weather import (
    ATTR_WEATHER_TEMPERATURE
)
from homeassistant.const import (
    HTTP_OK
)

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry



ATTR_MODE = 'mode'
ATTR_ROOM_TEMPERATURE = 'room_temperature'
ATTR_ROOM_TEMPERATURE_SET = 'room_temperature_set'
ATTR_ACS_TEMPERATURE = 'acs_temperature'
ATTR_ACS_TEMPERATURE_SET = 'acs_temperature_set'
ATTR_HEAT_PUMP_ON = 'heat_pump_on'
ATTR_EXTERNAL_TEMPERATURE = 'external_temperature'
ATTR_LAST_UPDATE = 'last_update'
CONF_DEVICE_ID = 'device_id'
ATTR_HEAT_PUMP_RESISTOR_ON = 'heat_pump_resistor_on' #heatingPumpResistorOn	
ATTR_HOLIDAY_ENABLED = "holidayEnabled"
ATTR_HOLIDAY_UNTIL = "holidayUntil"
ATTR_ANTIFREEZE_TEMP = "antiFreezeTemp"
ATTR_FLAME = 'flame'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=240)

class AristonApi:
    """Get the lastest data and updates the states."""
    
    API_URL_BASE = 'https://www.ariston-net.remotethermo.com/Account/Login?returnUrl='
    API_URL_NEGOTIATE = '/broker/negotiate?clientProtocol=1.5&ar.gateway={}'
    API_URL_DATA_DETAIL = '%2FPlantDashboard%2FGetPlantData%2F{}%3FzoneNum%3D%257B0%257D%26umsys%3Dsi%26firstRoundTrip%3Dtrue%26twoPhaseRefresh%3Dtrue%26completionToken%3D{}'

    def requests_retry_session( self,
        retries=3,
        backoff_factor=5,
        status_forcelist=(500, 502, 504),
        session=None,
    ):
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            method_whitelist=frozenset(['GET', 'POST']),
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def __init__(self, username, password, device_id):
        """Initialize the data object."""
        self._username = username
        self._password = password
        self._device_id = device_id
        self.data = {}

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        _LOGGER.debug("------- Updating Ariston sensor")
        
        # Get the completion token
        completion_token_url = "{}{}".format(
                            self.API_URL_BASE,
                            self.API_URL_NEGOTIATE.format(self._device_id)
                        )
        _LOGGER.debug("Completion token URL: %s", completion_token_url)
        payload = {'Email': self._username, 'Password': self._password}
        
        main_rsp = self.requests_retry_session().post(completion_token_url, data=payload)
        
        if main_rsp.status_code != HTTP_OK:
            _LOGGER.error("Invalid response: %s", main_rsp.status_code)
            return

        result = main_rsp.json()
        if "ConnectionId" in result:
            completion_token = result["ConnectionId"]
            _LOGGER.debug("Completion token: %s", completion_token)
            # Get the data
            data_url = "{}{}".format(
                            self.API_URL_BASE,
                            self.API_URL_DATA_DETAIL.format(self._device_id,completion_token)
                        )
            _LOGGER.debug("Data URL: %s", data_url)
            
            data_rsp = requests.post(data_url, data=payload)
            
            if data_rsp.status_code != HTTP_OK:
                _LOGGER.error("Invalid response: %s", data_rsp.status_code)
            data_result = data_rsp.json()
            self.set_data(data_result)
            _LOGGER.debug("JSON response: %s",data_result)
        else:
            _LOGGER.error("Invalid response: %s", main_rsp.status_code)

    def set_data(self, record):
        """Set data using the last record from API."""
        state = {}
        if 'mode' in record:
            if record['mode'] == 0:
                state[ATTR_MODE] = 'dhw'
            elif record['mode'] == 1:
                state[ATTR_MODE] = 'heating & dhw'
            elif record['mode'] == 2:
                state[ATTR_MODE] = 'heating only'
            elif record['mode'] == 3:
                state[ATTR_MODE] = 'cooling & dhw'
            elif record['mode'] == 5:
                state[ATTR_MODE] = 'off'
            else:
                state[ATTR_MODE] = record['mode']
        if 'zone' in record:
            zone = record['zone']
            if 'roomTemp' in zone:
                state[ATTR_ROOM_TEMPERATURE] = zone['roomTemp']
            if ATTR_ANTIFREEZE_TEMP in zone:
                state[ATTR_ANTIFREEZE_TEMP] = zone[ATTR_ANTIFREEZE_TEMP]
            if 'comfortTemp' in zone:
                if 'value' in zone['comfortTemp']:
                    state[ATTR_ROOM_TEMPERATURE_SET] =  zone["comfortTemp"]["value"]
        if ATTR_HOLIDAY_ENABLED in record:
            state[ATTR_HOLIDAY_ENABLED] = record[ATTR_HOLIDAY_ENABLED]
        if ATTR_HEAT_PUMP_RESISTOR_ON in record:
            state[ATTR_HEAT_PUMP_RESISTOR_ON] = record[ATTR_HEAT_PUMP_RESISTOR_ON]
        if 'dhwStorageTemp' in record:
            state[ATTR_ACS_TEMPERATURE] = record["dhwStorageTemp"]
        if 'dhwTemp' in record:
            if 'value' in record['dhwTemp']:
                state[ATTR_ACS_TEMPERATURE_SET] = record['dhwTemp']['value']
        if 'heatingPumpOn' in record:
            state[ATTR_HEAT_PUMP_ON] = record['heatingPumpOn']
        if 'outsideTemp' in record:
            state[ATTR_EXTERNAL_TEMPERATURE] = record['outsideTemp']
        if 'flameSensor' in record:
            state[ATTR_FLAME] = record['flameSensor']

        # Timestampp
        state[ATTR_LAST_UPDATE] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            
        self.data = state

    def get_data(self, variable):
        """Get the data."""
        return self.data.get(variable)
