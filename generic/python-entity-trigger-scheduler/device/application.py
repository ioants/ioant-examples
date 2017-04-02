# =============================================
# Adam Saxen
# Date: 2017-03-10
# Description: Trigger scheduler
# Schedule at what times it should trigger during the day
# =============================================
from ioant.sdk import IOAnt
import logging
import hashlib
import schedule
import time
logger = logging.getLogger(__name__)


def event_job():
    msg = ioant.create_message("Trigger")
    topic = ioant.get_topic_structure()
    configuration = ioant.get_configuration()

    for topic_configuration in configuration['trigger_topics']:
        topic['global'] = topic_configuration['global']
        topic['local'] = topic_configuration['local']
        topic['client_id'] = topic_configuration['client_id']
        ioant.publish(msg, topic)

    return


def setup(configuration):
    """ setup function """
    ioant.setup(configuration)
    for t in configuration['schedule']:
        logger.info("Scheduling time-event", {time:t})
        schedule.every().day.at(t).do(event_job)


def loop():
    """ Loop function """
    ioant.update_loop()
    schedule.run_pending()


def on_message(topic, message):
    print "message received!"


def on_connect():
    """ On connect function. Called when connected to broker """

# =============================================================================
# Above this line are mandatory functions
# =============================================================================
# Mandatory line
ioant = IOAnt(on_connect, on_message)
