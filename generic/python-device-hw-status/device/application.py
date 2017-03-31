# =============================================
# Benny Saxen
# Date: 2017-03-31
# Description: Device hw status
#   - CPU temperature
# =============================================
from ioant.sdk import IOAnt
import logging
import hashlib
logger = logging.getLogger(__name__)


def setup(configuration):
    """ setup function """
    ioant.setup(configuration)


def loop():
    """ Loop function """
    ioant.update_loop()
    configuration = ioant.get_configuration()
    msg = ioant.create_message("Temperature")
    # msg.unit = msg.Unit.Value("FAHRENHEIT")
    msg.unit = msg.Unit.Value("CELSIUS")

    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as temp:
            curCtemp = float(temp.read()) / 1000
            curFtemp = ((curCtemp / 5) * 9) + 32
            #print ("C:", curCtemp, " F:", curFtemp)
            msg.unit = msg.Unit.Value("CELSIUS")
            msg.value = curCtemp
    except:
        msg.value = 0.123
    # publish with device topic
    #ioant.publish(msg)
    # pr publish with custom topic
    topic = ioant.get_topic_structure()
    topic['global'] = configuration["publish_topic"]["CPUtemp"]["global"]
    topic['local'] =  configuration["publish_topic"]["CPUtemp"]["local"]
    topic['client_id'] =  configuration["publish_topic"]["CPUtemp"]["client_id"]
    topic['stream_index'] =  configuration["publish_topic"]["CPUtemp"]["stream_index"]
    ioant.publish(msg,topic)


def on_message(topic, message):
    if "Temperature" == ioant.get_message_type_name(topic[message_type]):
        logger.debug("Message received of type temperature")
        logger.debug("Contains value:" + str(message.value))


def on_connect():
    """ On connect function. Called when connected to broker """

# =============================================================================
# Above this line are mandatory functions
# =============================================================================
# Mandatory line
ioant = IOAnt(on_connect, on_message)
