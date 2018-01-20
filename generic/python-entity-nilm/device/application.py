# =============================================
# Application: NILM Analysis
# Author: Benny Saxen
# Date: 2018-01-20
# Description:
# =============================================
from ioant.sdk import IOAnt
import logging
logger = logging.getLogger(__name__)

prev_value = 0.0
new_value = 0.0
ackum = 0.0
#=====================================================
def subscribe_to_topic(msgt):
    configuration = ioant.get_configuration()
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["subscribe_topic"]["global"]
    topic['local'] = configuration["subscribe_topic"]["local"]
    topic['client_id'] = configuration["subscribe_topic"]["client_id"]
    topic['message_type'] = ioant.get_message_type(msgt)
    topic['stream_index'] = configuration["subscribe_topic"]["stream_index"]
    print "Subscribe to: " + str(topic)
    ioant.subscribe(topic)

def setup(configuration):
    """ setup function """
    ioant.setup(configuration)

def loop():
    """ Loop function """
    ioant.update_loop()

def on_message(topic, message):
    global prev_value
    global new_value
    global ackum
    prev_value = new_value
    new_value = message.value
    if prev_value > 0.0:
        delta = prev_value - new_value
        ackum = ackum + delta
        print delta
        print ackum

def on_connect():
    """ On connect function. Called when connected to broker """
    subscribe_to_topic("ElectricPower")

# =============================================================================
# Above this line are mandatory functions
# =============================================================================
# Mandatory line
ioant = IOAnt(on_connect, on_message)
