# =============================================
# Benny Saxen
# Date: 2017-03-31
# Description: Device hw status
#   - CPU temperature
#
# sudo apt install lm-sensors
# =============================================
from ioant.sdk import IOAnt
import logging
import hashlib
import os
import sys
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

    if configuration["hw"] == "raspbian":
        try:
            with open('/sys/class/thermal/thermal_zone0/temp') as temp:
                curCtemp = float(temp.read()) / 1000
                curFtemp = ((curCtemp / 5) * 9) + 32
                #print ("C:", curCtemp, " F:", curFtemp)
                msg.unit = msg.Unit.Value("CELSIUS")
                msg.value = curCtemp
        except:
            msg.value = 0.111

    if configuration["hw"] == "debian":
        try:
            os.system("sensors | grep -oP 'Core 0.*?\+\K[0-9.]+' > sensor.txt")
            with open('sensor.txt') as temp:
                curCtemp = float(temp.read())
                curFtemp = ((curCtemp / 5) * 9) + 32
                #print ("C:", curCtemp, " F:", curFtemp)
                msg.unit = msg.Unit.Value("CELSIUS")
                msg.value = curCtemp
        except:
            e = sys.exc_info()[0]
            print e
            msg.value = 0.222

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
