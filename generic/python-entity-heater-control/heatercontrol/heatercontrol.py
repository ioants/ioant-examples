# =============================================
# File: heatercontrol.py
# Author: Benny Saxen
# Date: 2018-09-28
# Description: IOANT heater control algorithm
# 90 degrees <=> 1152/4 steps = 288
# =============================================
from ioant.sdk import IOAnt
import logging
import hashlib
import math
import urllib
import urllib2

logger = logging.getLogger(__name__)

#===================================================
def spacecollapse_op1 ( label, typ, value ):
#===================================================
	url = 'http://spacecollapse.simuino.com/scServer.php'
	data = {}
	data['op'] = 1
	data['label'] = label
	data['type'] = typ
	data['value'] = value

	values = urllib.urlencode(data)
	req = url + '?' + values
	try: response = urllib2.urlopen(req)
	except urllib2.URLError as e:
		print e.reason
	the_page = response.read()

#===================================================
def spacecollapse_op2 ( label, param ):
#===================================================
	url = 'http://spacecollapse.simuino.com/scServer.php'
	data = {}
	data['op'] = 2
	data['label'] = label
	data['param'] = param

	values = urllib.urlencode(data)
	req = url + '?' + values
	try: response = urllib2.urlopen(req)
	except urllib2.URLError as e:
		print e.reason
	the_page = response.read()

#=====================================================
def write_position(pos):
    try:
        f = open("position.work",'w')
        s = str(pos)
        f.write(s)
        f.close()
    except:
        print "ERROR write to position file"
    return
#=====================================================
def read_position():
    try:
        f = open("position.work",'r')
        pos = int(f.read())
        f.close()
    except:
        print("WARNING Create position file")
        f = open("position.work",'w')
        s = str(0)
        f.write(s)
        f.close()
        pos = 0
    return pos
#=====================================================
def write_history(message):
    try:
        f = open("history.work",'a')
        f.write(message)
        f.write('\n')
        f.close()
    except:
        print "ERROR write to history file"
    return
#=====================================================
def write_log(message):
    try:
        f = open("log.work",'a')
        f.write(message)
        f.write('\n')
        f.close()
    except:
        print "ERROR write to log file"
    return
#=====================================================
def write_ML(pos,temp):
    try:
	message = str(pos) + " " + str(temp)
        f = open("ML.work",'a')
        f.write(message)
        f.write('\n')
        f.close()
    except:
        print "ERROR write to ML file"
    return

#=====================================================
def init_history():
    try:
        f = open("history.work",'w')
        f.write("===== History =====")
        f.write('\n')
        f.close()
    except:
        print "ERROR init history file"
    return
#=====================================================
def init_log():
    try:
        f = open("log.work",'w')
        f.write("===== Log =====")
        f.write('\n')
        f.close()
    except:
        print "ERROR init log file"
    return
#=====================================================
def publishStepperMsg(steps, direction):
    global g_stepperpos
    msg = "ORDER steps to move: "+str(steps) + " dir:" + str(direction)
    write_history(msg)
    print msg
    #return
    if steps > 500: # same limit as stepper device
        print "Too many steps "+str(steps)
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
def init_log():
    try:
        f = open("log.work",'w')
        f.write("===== Log =====")
        f.write('\n')
        f.close()
    except:
        print "ERROR init log file"
    return
    write_position(g_stepperpos)

#=====================================================
def heater_model():

    global g_minsteps,g_maxsteps,g_defsteps
    global g_minsmoke
    global g_mintemp,g_maxtemp
    global g_minheat,g_maxheat
    global g_x_0,g_y_0
    global g_onofftime
    global g_relax
    global g_inertia
    global g_stepperpos

    global r_uptime
    global r_state
    global r_inertia

    global temperature_indoor
    global temperature_outdoor
    global temperature_water_in
    global temperature_water_out
    global temperature_smoke

    global timeout_temperature_indoor
    global timeout_temperature_outdoor
    global timeout_temperature_water_in
    global timeout_temperature_water_out
    global timeout_temperature_smoke

    init_log()

    CLOCKWISE = 0
    COUNTERCLOCKWISE = 1

    coeff1 = (g_maxheat - g_y_0)/(g_mintemp - g_x_0)
    mconst1 = g_y_0 - coeff1*g_x_0

    coeff2 = (g_y_0 - g_minheat)/(g_x_0 - g_maxtemp)
    mconst2 = g_minheat - coeff2*g_maxtemp

    r_state = 0
    y = 999
    energy = 999
    steps = 999

    write_log("===== Heater Model =====")

    timeout_temperature_indoor -= 1
    timeout_temperature_outdoor -= 1
    timeout_temperature_water_in -= 1
    timeout_temperature_water_out -= 1
    timeout_temperature_smoke -= 1

    # If necessary data not available: do nothing
    ndi = 0
    if temperature_outdoor == 999:
	message = "No data - temperature_outdoor"
	write_log(message)
	write_history(message)
	ndi = ndi + 1

    if temperature_water_out == 999:
	message = "No data - temperature_water_out"
	write_log(message)
	write_history(message)
	ndi = ndi + 1

    if temperature_water_in == 999:
	message = "No data - temperature_water_in"
	write_log(message)
	write_history(message)
	ndi = ndi + 1

    if temperature_smoke == 999:
	message = "No data - temperature_smoke"
	write_log(message)
	write_history(message)
	ndi = ndi + 1


    #====== All necessary data recieved
    if ndi == 0:
	r_state = 1
	
    if timeout_temperature_indoor < 1:
	message = "Old data - temperature_indoor " + str(timeout_temperature_indoor)
	write_log(message)
	write_history(message)
	r_state = 0
    if timeout_temperature_outdoor < 1:
	message = "Old data - temperature_outdoor " + str(timeout_temperature_outdoor)
	write_log(message)
	write_history(message)
	r_state = 0
    if timeout_temperature_water_in < 1:
	message = "Old data - temperature_water_in " + str(timeout_temperature_water_in)
	write_log(message)
	write_history(message)
	r_state = 0
    if timeout_temperature_water_out < 1:
	message = "Old data - temperature_water_out " + str(timeout_temperature_water_out)
	write_log(message)
	write_history(message)
	r_state = 0
    if timeout_temperature_smoke < 1:
	message = "Old data - temperature_smoke " + str(timeout_temperature_smoke)
	write_log(message)
	write_history(message)
	r_state = 0
#========================================================
# All input data available. Find status of heater
    if r_state == 1:
#========================================================
	write_log("Enter state 1")
	#write_history("State 1")
    #====== Heater is on
    	if temperature_smoke > g_minsmoke:
            r_uptime = r_uptime + 1
            if r_uptime > g_onofftime:
            	r_uptime = g_onofftime

            if r_uptime < g_onofftime:
            	r_state = 3
            if r_uptime == g_onofftime:
            	r_state = 4

    	# Heater is off
    	else:
            r_state = 2

#========================================================
# Heater is OFF
    if r_state == 2:
#========================================================
	write_log("Enter state 2")
	#write_history("State 2")
	r_uptime = r_uptime -1
	if r_uptime < 1:
		r_uptime = 0
		if g_stepperpos > 0:
		    publishStepperMsg(g_stepperpos, CLOCKWISE)
		    g_stepperpos = 0
	            write_log("Stepper position reset to 0")

#========================================================
# Heater starting up
    if r_state == 3:
#========================================================
	write_log("Enter state 3")
	#write_history("State 3")
	write_log("Do nothing")
#========================================================
# The heater is on and max heated
    if r_state == 4:
#========================================================
	write_log("Enter state 4")
        #write_history("State 4")
	t_temperature_outdoor = temperature_outdoor
	if temperature_outdoor > g_maxtemp:
        	t_temperature_outdoor = g_maxtemp
		msg = "Max limit reached - temperature_outdoor " + str(temperature_outdoor)
	        write_log(msg)
		write_history(msg)
        if temperature_outdoor < g_mintemp:
                t_temperature_outdoor = g_mintemp
		msg = "Min limit reached - temperature_outdoor " + str(temperature_outdoor)
	        write_log(msg)
		write_history(msg)

        # Expected water out temperature from heater
        if t_temperature_outdoor < g_x_0:
                y = coeff1*t_temperature_outdoor + mconst1
        else:
                y = coeff2*t_temperature_outdoor + mconst2

        # if target temperature is below typical indoor temperature - do nothing
        if y < g_minheat:
            msg = "Target temperature to low " + str(y)
	    write_log(msg)
	    write_history(msg)
            y = g_minheat

        if y > g_maxheat:
            msg = "Target temperature to high " + str(y)
	    write_log(msg)
            write_history(msg) 
            y = g_maxheat

        # Energy outage
        energy = temperature_water_out - temperature_water_in
        steps = (int)(abs(y - temperature_water_out)*g_relax)
	if y > temperature_water_out:
		msg = "Increase heater " + str(steps)
		write_log(msg)
		#write_history(msg) 
	if y < temperature_water_out:
		msg = "Decrease heater " + str(steps)
		write_log(msg)
		#write_history(msg) 

        if energy < 0 and y < temperature_water_out:
            steps = 0
            write_log("Negative energy - cooling not possible - RETURN")
	    write_history("Negative energy - cooling not possible - RETURN")

        # Restrict steps to max Steps
        if steps > g_maxsteps:
            msg = "Upper step limit reached = " + str(steps)
	    write_log(msg)
            steps = g_defsteps
	
        # Restrict steps to min Steps
        if steps < g_minsteps:
            msg = "Lower step limit reached = " + str(steps)
	    write_log(msg)

	# steps - ok, smoke temp - ok, inertia - ok
        if steps > g_minsteps and temperature_smoke > g_minsmoke and r_inertia == 0:
            ok = 0
	    # increase water-out-temp and indoor temp is below 20
            if(y > temperature_water_out and temperature_indoor < 20):
                direction = COUNTERCLOCKWISE
                msg = "Intention: Increase heat = " + str(steps)
		write_log(msg)
		write_history(msg)
                slimit = g_stepperpos + steps
                if slimit < 288:
		    write_ML(g_stepperpos,temperature_water_out)
                    g_stepperpos = slimit
                    ok = 1;
		    write_log("Stepper moved COUNTERCLOCKWISE")
		else:
		    write_log("Stepper position to high")
		    write_history("Stepper position to high")
            else:
                direction = CLOCKWISE
                msg = "Intention: Decrease heat = " + str(steps)
		write_log(msg)
                if g_stepperpos > 0:
		    write_ML(g_stepperpos,temperature_water_out)
                    g_stepperpos = g_stepperpos - steps
                    ok = 1;
		    write_log("Stepper moved CLOCKWISE")
		else:
		    write_log("Stepper position to low")
		    write_history("Stepper position to low")

            # Execute order to stepper motor
            if ok == 1:
                r_inertia = g_inertia
                publishStepperMsg(steps, direction)
		status = str(r_uptime) + " state " + str(r_state) + " target=" + str(y) + "("+str(temperature_water_out)+")" + " Energy " + str(energy) + " countdown " + str(r_inertia) + " steps " + str(steps)
                status = status + "Pos=" + str(g_stepperpos) + " indoor "
                write_history(status)


#========================================================================
    status = str(r_uptime) + " state " + str(r_state) + " target=" + str(y) + "("+str(temperature_water_out)+")" + " Energy " + str(energy) + " countdown " + str(r_inertia) + " steps " + str(steps)
    status = status + "Pos=" + str(g_stepperpos) + " indoor " + str(timeout_temperature_indoor) + " outdoor " + str(timeout_temperature_outdoor)
    print status
    write_log(status)

    spacecollapse_op1('kil_kvv32_heatercontrol_status','status', r_state)
    spacecollapse_op1('kil_kvv32_heatercontrol_position','position', g_stepperpos)
    spacecollapse_op1('kil_kvv32_heatercontrol_inertia','inertia', r_inertia)
    spacecollapse_op1('kil_kvv32_heatercontrol_uptime','uptime', r_uptime)
    spacecollapse_op1('kil_kvv32_heatercontrol_target','target', y)
    spacecollapse_op1('kil_kvv32_heatercontrol_steps','steps', steps)
    spacecollapse_op1('kil_kvv32_heatercontrol_energy','energy', energy)
    spacecollapse_op1('kil_kvv32_heatercontrol_timeout_indoor','timeout_indoor', timeout_temperature_indoor)
    spacecollapse_op1('kil_kvv32_heatercontrol_timeout_outdoor','timeout_outdoor', timeout_temperature_outdoor)
    spacecollapse_op1('kil_kvv32_heatercontrol_timeout_water_in','timeout_water_in', timeout_temperature_water_in)
    spacecollapse_op1('kil_kvv32_heatercontrol_timeout_water_out','timeout_water_out', timeout_temperature_water_out)
    spacecollapse_op1('kil_kvv32_heatercontrol_timeout_smoke','timeout_smoke', timeout_temperature_smoke)

    return


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
    # Configuration
    global g_minsteps,g_maxsteps,g_defsteps
    global g_minsmoke
    global g_mintemp,g_maxtemp
    global g_minheat,g_maxheat
    global g_x_0,g_y_0
    global g_onofftime
    global g_relax
    global g_inertia
    global g_stepperpos

    global r_uptime
    global r_state
    global r_inertia

    g_minsteps = 5
    g_maxsteps = 30
    g_defsteps = 10
    g_minsmoke = 27
    g_mintemp = -7
    g_maxtemp = 10
    g_minheat = 20
    g_maxheat = 40
    g_x_0 = 0
    g_y_0 = 35
    g_onofftime = 3600
    g_relax = 3.0
    g_inertia = 130
    g_stepperpos = 0

    g_stepperpos = read_position()

    global temperature_indoor
    global temperature_outdoor
    global temperature_water_in
    global temperature_water_out
    global temperature_smoke

    temperature_indoor    = 999
    temperature_outdoor   = 999
    temperature_water_in  = 999
    temperature_water_out = 999
    temperature_smoke     = 999
	
    global timeout_temperature_indoor
    global timeout_temperature_outdoor
    global timeout_temperature_water_in
    global timeout_temperature_water_out
    global timeout_temperature_smoke

    timeout_temperature_indoor = 60
    timeout_temperature_outdoor = 60
    timeout_temperature_water_in = 60
    timeout_temperature_water_out = 60
    timeout_temperature_smoke = 60
	
    ioant.setup(configuration)

    configuration = ioant.get_configuration()

    g_minsteps = int(configuration["algorithm"]["minsteps"])
    g_maxsteps = int(configuration["algorithm"]["maxsteps"])
    g_defsteps = int(configuration["algorithm"]["defsteps"])

    g_minsmoke = float(configuration["algorithm"]["minsmoke"])

    g_mintemp = float(configuration["algorithm"]["mintemp"])
    g_maxtemp = float(configuration["algorithm"]["maxtemp"])

    g_minheat = float(configuration["algorithm"]["minheat"])
    g_maxheat = float(configuration["algorithm"]["maxheat"])

    g_x_0 = float(configuration["algorithm"]["x_0"])
    g_y_0 = float(configuration["algorithm"]["y_0"])

    g_onofftime = int(configuration["algorithm"]["onofftime"])

    g_inertia = int(configuration["algorithm"]["inertia"])

    g_relax = float(configuration["algorithm"]["relax"])

    r_state = 0
    r_inertia = g_inertia
    r_uptime = g_onofftime

    spacecollapse_op1('kil_kvv32_heatercontrol_status','status', r_state)
    spacecollapse_op1('kil_kvv32_heatercontrol_position','position', g_stepperpos)
    spacecollapse_op1('kil_kvv32_heatercontrol_inertia','inertia', r_inertia)
    spacecollapse_op1('kil_kvv32_heatercontrol_uptime','uptime', r_uptime)
    spacecollapse_op1('kil_kvv32_heatercontrol_target','target', 0)
    spacecollapse_op1('kil_kvv32_heatercontrol_steps','steps', 0)
    spacecollapse_op1('kil_kvv32_heatercontrol_energy','energy', 0)

    init_log()
    init_history()

#=====================================================
def loop():
    global r_inertia

    ioant.update_loop()
    if r_inertia > 0:
        r_inertia -= 1

    heater_model()

#=====================================================
def on_message(topic, message):
    global hash_indoor
    global hash_outdoor
    global hash_water_in
    global hash_water_out
    global hash_smoke

    global temperature_indoor
    global temperature_outdoor
    global temperature_water_in
    global temperature_water_out
    global temperature_smoke
	
    global timeout_temperature_indoor
    global timeout_temperature_outdoor
    global timeout_temperature_water_in
    global timeout_temperature_water_out
    global timeout_temperature_smoke

    """ Message function. Handles recieved message from broker """

    if topic["message_type"] == ioant.get_message_type("Temperature"):
        shash = getTopicHash(topic)
        #logging.info("Temp = "+str(message.value)+" hash="+str(shash))
        if shash == hash_indoor:
            print "===> indoor " + str(message.value)
            temperature_indoor = message.value
	    timeout_temperature_indoor = 60
        if shash == hash_outdoor:
            print "===> outdoor " + str(message.value)
            temperature_outdoor = message.value
	    timeout_temperature_outdoor = 60
        if shash == hash_water_in:
            print "===> water in " + str(message.value)
            temperature_water_in = message.value
	    timeout_temperature_water_in = 60
        if shash == hash_water_out:
            print "===> water out " + str(message.value)
            temperature_water_out = message.value
	    timeout_temperature_water_out = 60
        if shash == hash_smoke:
            print "===> smoke " + str(message.value)
            temperature_smoke = message.value
	    timeout_temperature_smoke = 60

    #if "Temperature" == ioant.get_message_type_name(topic[message_type]):

#=====================================================
def on_connect():
    """ On connect function. Called when connected to broker """
    global hash_indoor
    global hash_outdoor
    global hash_water_in
    global hash_water_out
    global hash_smoke

    # There is now a connection
    hash_indoor    = subscribe_to_topic("indoor","Temperature")
    hash_outdoor   = subscribe_to_topic("outdoor","Temperature")
    hash_water_in  = subscribe_to_topic("water_in","Temperature")
    hash_water_out = subscribe_to_topic("water_out","Temperature")
    hash_smoke     = subscribe_to_topic("smoke","Temperature")

# =============================================================================
# Above this line are mandatory functions
# =============================================================================
# Mandatory line
ioant = IOAnt(on_connect, on_message)
