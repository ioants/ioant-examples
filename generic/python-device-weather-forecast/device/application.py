# =============================================
# Adam Saxen
# Date: 2017-04-08
# Description: Weather forecast API collector
# Collect forecast data from external weather api
# =============================================
from ioant.sdk import IOAnt
import logging
import schedule
import time
import requests
import xmltodict
from datetime import datetime, timedelta
import dateutil.parser
logger = logging.getLogger(__name__)

global forecast_points_dict
API_url_list = []
MAP_FIELD_NAMES_TO_MESSAGE_NAMES = {'temperature': 'Temperature', 'pressure' : 'AtmosphericPressure', 'humidity': "Humidity"}

def event_job():
    """ Perform a data request and translate to and publish as ioant messages """
    for url_request in API_url_list:
        res = retrieve_data(url_request)
        for value_field in url_request['values_of_interest']:
            logger.info('Messagename:{0}, value: {1}'.format(MAP_FIELD_NAMES_TO_MESSAGE_NAMES.get(value_field), res.get(value_field)))
            msg = ioant.create_message(MAP_FIELD_NAMES_TO_MESSAGE_NAMES.get(value_field))
            msg.value = float(res.get(value_field))
            t = ioant.get_topic_structure()
            t['local'] = url_request['tag']
            #ioant.publish(msg, t)


def setup(configuration):
    """ setup function """
    ioant.setup(configuration)
    forecast_points = configuration['forecast_points']

    """Build list of API URLs to call"""
    for point in forecast_points:
        TEMP_OBJECT = {}
        TEMP_OBJECT['tag'] = point['tag']
        TEMP_OBJECT['number_of_days'] = point['number_of_days']
        TEMP_OBJECT['values_of_interest'] = point['values_of_interest']
        TEMP_OBJECT['api_url'] = 'http://api.met.no/weatherapi/locationforecast/1.9/?lat={0};lon={1};msl={2}'.format(point['longitude'],
                                                                                                                     point['latitude'],
                                                                                                                     point['meters_above_sealevel'])
        API_url_list.append(TEMP_OBJECT)

    schedule.every().day.at("23:04").do(event_job)


def loop():
    """ Loop function """
    ioant.update_loop()
    schedule.run_pending()


def on_message(topic, message):
    logger.info("message received!")

def on_connect():
    """ On connect function. Called when connected to broker """

def retrieve_data(request):
    r = requests.get(request['api_url'])
    doctest = xmltodict.parse(r.text)
    number_of_forecasts = len(doctest['weatherdata']['product']['time'])
    #d_string = 'Retrieving weather forecast({0}) - found {1}'.format(request['api_url'], str(number_of_forecasts))
    logger.debug('Retrieving weather forecast({0}) - found {1}'.format(request['api_url'], str(number_of_forecasts)))
    results = {}
    now_date = datetime.utcnow()
    end_date = now_date + timedelta(days=request['number_of_days'])
    for forecast in doctest['weatherdata']['product']['time']:
        # Only keep aggregations per day
        if forecast['@from'] == forecast['@to']:
            # Filter out events according to number_of_days in config
            d = dateutil.parser.parse(forecast['@from'])
            if d.day == end_date.day:
                logger.info(d.day)
                logger.info(forecast['@from'])
                results['temperature'] = forecast['location']['temperature']['@value']
                results['humidity'] = forecast['location']['humidity']['@value']
                results['pressure'] = forecast['location']['pressure']['@value']
                return results


# =============================================================================
# Below this line are mandatory functions
# =============================================================================
# Mandatory line
ioant = IOAnt(on_connect, on_message)
