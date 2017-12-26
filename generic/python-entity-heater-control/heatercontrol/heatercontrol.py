# =============================================
# File: heatercontrol.py
# Author: Benny Saxen
# Date: 2017-12-26
# Description: IOANT heater control algorithm
# =============================================
from ioant.sdk import IOAnt
import logging
import hashlib
import math
logger = logging.getLogger(__name__)

#=====================================================
def read_status():
    try:
        f = open("status.work",'r')
        pos = int(f.read())
        f.close()
    except:
        print("WARNING Create status file")
        f = open("status.work",'w')
        s = str(0)
        f.write(s)
        f.close()
    return

#=====================================================
def write_status(status):
    try:
        f = open("status.work",'w')
        f.write(status)
        f.close()
    except:
        print "ERROR write to status file"
    return

#=====================================================
def publishStepperMsg(steps, direction):
    print "ORDER steps to move: "+str(steps) + " dir:" + str(direction)
    #return
    if steps > 100:
        return
    configuration = ioant.get_configuration()
    out_msg = ioant.create_message("RunStepperMotorRaw")
    out_msg.direction = direction
    out_msg.delay_between_steps = 5
    out_msg.number_of_step = steps
    out_msg.step_size = out_msg.StepSize.Value("FULL_STEP")
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["publish_topic"]["stepper"]["global"]
    topic['local'] = configuration["publish_topic"]["stepper"]["local"]
    topic['client_id'] = configuration["publish_topic"]["stepper"]["client_id"]
    topic['stream_index'] = 0
    ioant.publish(out_msg, topic)

#=====================================================
def heater_model():

    global etc
    global adj
    global h_state
    global uptime

    CLOCKWISE = 0
    COUNTERCLOCKWISE = 1

    configuration = ioant.get_configuration()

    minstep  = float(configuration["algorithm"]["minstep"])
    minsmoke = float(configuration["algorithm"]["minsmoke"])


    global temperature_indoor
    global temperature_outdoor
    global temperature_water_in
    global temperature_water_out
    global temperature_smoke

    if temperature_outdoor == 999:
        return
    if temperature_water_out == 999:
        return
    if temperature_smoke == 999:
        return

    # READY  (all necessary data recieved)
    h_state = 2

    if temperature_smoke > minsmoke:
        uptime = uptime + 1
        # RUNNING  (the heater is on and  )
        if uptime < 3601:
            # STARTING  (the heater is on and under start-up )
            h_state = 3
        if uptime > 3600:
            # RUNNING  (the heater is on and max heated  )
            h_state = 4
        # wraparound counter
        if uptime > 99999:
            uptime = 3600
    # Heater is off
    else:
        if h_state == 4:
            h_state = 5
            uptime = 3600

        uptime = uptime -1

        if uptime < 1:
            uptime = 0

    # RUNNING  (the heater is on and max heated  )
    if h_state == 4:

        # Expected water out temperature from heater
        y = -1.0*temperature_outdoor + 37

        # if target temperature is below typical indoor temperature - do nothing
        if y < 20:
            status = "Target heat to low " + str(y)
            write_status(status)
            return
        # Energy outage
        energy = temperature_water_out - temperature_water_in

        steps = (int)(abs(y - temperature_water_out)*adj)

        # Upper limit for steps in one order
        if steps > 30:
            status = "steps overflow " + str(steps)
            write_status(status)
            return

        if steps > minstep and temperature_smoke > minsmoke and etc == 0:
            if(y > temperature_water_out):
                direction = COUNTERCLOCKWISE
                print "Direction is COUNTERCLOCKWISE (increase) " + str(steps)
            else:
                direction = CLOCKWISE
                print "Direction is CLOCKWISE (decrease) " + str(steps)

            etc = float(configuration["algorithm"]["inertia"])

            publishStepperMsg(steps, direction)
        else:
            status = str(uptime) + " state " + str(h_state) + " " + str(y) + " Energy " + str(energy) + " countdown " + str(etc) + " steps " + str(steps)
            write_status(status)
            print status
    else:
        status = "uptime " + str(uptime) + " state " + str(h_state)
        write_status(status)
        print status
#=====================================================
def getTopicHash(topic):
    res = topic['top'] + topic['global'] + topic['local'] + topic['client_id'] + str(topic['message_type']) + str(topic['stream_index'])
    tres = hash(res)
    tres = tres% 10**8
    return tres

#=====================================================
def subscribe_to_topic(par,msgt):
    configuration = ioant.get_configuration()
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["subscribe_topic"][par]["global"]
    topic['local'] = configuration["subscribe_topic"][par]["local"]
    topic['client_id'] = configuration["subscribe_topic"][par]["client_id"]
    topic['message_type'] = ioant.get_message_type(msgt)
    topic['stream_index'] = configuration["subscribe_topic"][par]["stream_index"]
    print "Subscribe to: " + str(topic)
    ioant.subscribe(topic)
    shash = getTopicHash(topic)
    return shash

#=====================================================
def setup(configuration):
    """ setup function """
    global etc
    global adj
    global h_state
    global uptime
    #current_shunt_position = read_shunt_position()
    #print "Initial shunt position: " + str(current_shunt_position)
    etc = 999
    adj = 3.0
    global temperature_indoor
    global temperature_outdoor
    global temperature_water_in
    global temperature_water_out
    global temperature_smoke
    global temperature_target

    temperature_indoor    = 999
    temperature_outdoor   = 999
    temperature_water_in  = 999
    temperature_water_out = 999
    temperature_smoke     = 999
    temperature_target    = 999

    ioant.setup(configuration)

    configuration = ioant.get_configuration()
    etc = float(configuration["algorithm"]["inertia"])

    # Initiated
    h_state = 1
    uptime = 3600
#=====================================================
def loop():
    """ Loop function """
    global etc
    ioant.update_loop()
    if etc > 0:
        etc -= 1

    heater_model()

#=====================================================
def on_message(topic, message):
    global hash_indoor
    global hash_outdoor
    global hash_water_in
    global hash_water_out
    global hash_smoke
    global hash_target

    global temperature_indoor
    global temperature_outdoor
    global temperature_water_in
    global temperature_water_out
    global temperature_smoke
    global temperature_target

    """ Message function. Handles recieved message from broker """

    if topic["message_type"] == ioant.get_message_type("Trigger"):
        shash = getTopicHash(topic)
        if shash == hash_target:
            print "target"
            temperature_target = float(message.extra)

    if topic["message_type"] == ioant.get_message_type("Temperature"):
        shash = getTopicHash(topic)
        #logging.info("Temp = "+str(message.value)+" hash="+str(shash))
        if shash == hash_indoor:
            print "===> indoor " + str(message.value)
            temperature_indoor = message.value
        if shash == hash_outdoor:
            print "===> outdoor " + str(message.value)
            temperature_outdoor = message.value
        if shash == hash_water_in:
            print "===> water in " + str(message.value)
            temperature_water_in = message.value
        if shash == hash_water_out:
            print "===> water out " + str(message.value)
            temperature_water_out = message.value
        if shash == hash_smoke:
            print "===> smoke " + str(message.value)
            temperature_smoke = message.value

    #if "Temperature" == ioant.get_message_type_name(topic[message_type]):

#=====================================================
def on_connect():
    """ On connect function. Called when connected to broker """
    global hash_indoor
    global hash_outdoor
    global hash_water_in
    global hash_water_out
    global hash_smoke
    global hash_target

    # There is now a connection
    hash_indoor    = subscribe_to_topic("indoor","Temperature")
    hash_outdoor   = subscribe_to_topic("outdoor","Temperature")
    hash_water_in  = subscribe_to_topic("water_in","Temperature")
    hash_water_out = subscribe_to_topic("water_out","Temperature")
    hash_smoke     = subscribe_to_topic("smoke","Temperature")

    hash_target   = 0 #subscribe_to_topic("target","Trigger")

# =============================================================================
# Above this line are mandatory functions
# =============================================================================
# Mandatory line
ioant = IOAnt(on_connect, on_message)
