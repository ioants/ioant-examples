# =============================================
# Adam Saxen
# Date: 2017-03-10
# Description: Simple boilerplate on how to publish
# and subscribe on messages
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
    msg = ioant.create_message("Trigger")
    topic = ioant.get_topic_structure()
    configuration = ioant.get_configuration()
    topic['global'] = configuration['trigger_topic']['global']
    topic['local'] = configuration['trigger_topic']['local']
    topic['client_id'] = configuration['trigger_topic']['client_id']

    # publish with device topic
    ioant.publish(msg, topic)


def on_message(topic, message):
    print "message received!"


def on_connect():
    """ On connect function. Called when connected to broker """

# =============================================================================
# Above this line are mandatory functions
# =============================================================================
# Mandatory line
ioant = IOAnt(on_connect, on_message)
