# =============================================
# Adam Saxen
# Date: 2017-09-16
# Description: API.ai webhook example with IOAnt support
# =============================================

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

import json
import os
import thread
import server

from ioant.sdk import IOAnt
import logging
import hashlib
logger = logging.getLogger(__name__)

def intent_request(req):
    """ Handles and responds on webhook request from API.ai """
    action = req.get("result").get("action")
    print("request ioant action:", action)

    topic = ioant.get_topic_structure()
    #topic['global'] = configuration["api"]["ai"]["global"]
    #topic['local'] =  configuration["publish_topic"]["CPUtemp"]["local"]
    topic['client_id'] =  "bot1"
    #topic['stream_index'] =  configuration["publish_topic"]["CPUtemp"]["stream_index"]

    if action == "light.on":
        action_text = "light on"
        msg = ioant.create_message("Switch")
        msg.state = True
        ioant.publish(msg,topic)
    elif action == "light.off":
        action_text = "light off"
        msg = ioant.create_message("Switch")
        msg.state = False
        ioant.publish(msg,topic)
    else:
        return {}

    print("Action chosen:" + action_text)

    # Dict that will be returned as JSON to API.ai
    return {
        "speech": action_text,
        "displayText": action_text,
        # "data": data,
        # "contextOut": [],
        "source": ioant.get_configuration()["app_name"]
    }


def setup(configuration):
    """ setup function """
    ioant.setup(configuration)
    thread.start_new_thread(server.init_server,(configuration["web_server"]["port"],
                                                intent_request))
    print("Setup Done")


def loop():
    """ Loop function """
    ioant.update_loop()


def on_message(topic, message):
    if "Temperature" == ioant.get_message_type_name(topic[message_type]):
        logger.debug("Message received of type temperature")
        logger.debug("Contains value:" + str(message.value))


def on_connect():
    """ On connect function. Called when connected to broker """


ioant = IOAnt(on_connect, on_message)
