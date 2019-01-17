# =============================================
# File: heatercontrol.py
# Author: Benny Saxen
# Date: 2019-01-17
# Description: IOANT heater control algorithm
# Next Generation
# 90 degrees <=> 1152/4 steps = 288
# =============================================
from ioant.sdk import IOAnt
import logging
import hashlib
import math
import urllib
import urllib2
import time
import datetime

logger = logging.getLogger(__name__)
temperature_indoor    = 999
temperature_outdoor   = 999
temperature_water_in  = 999
temperature_water_out = 999
temperature_smoke     = 999
STATE_INIT = 0
STATE_OFF = 1
STATE_WARMING = 2
STATE_ON = 3
MODE_OFFLINE = 1
MODE_ONLINE = 2
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
g_relax = 3.0
timeout_temperature_indoor = 60
timeout_temperature_outdoor = 60
timeout_temperature_water_in = 60
timeout_temperature_water_out = 60
timeout_temperature_smoke = 60
g_counter = 0
#===================================================
def publishGowData( ipayload, n ):
#===================================================
        global g_gow_server
	global g_period
	global g_gow_topic
	
	url = g_gow_server
	server = 'gowServer.php'
	data = {}
	# meta data
	data['do']     = 'data'
	data['topic']  = g_gow_topic
	data['no']     = n
	data['wrap']   = 999999
	data['ts']     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	data['period'] = g_period
	data['hw']     = 'python'
	data['hash']   = 'nohash'
	# payload
	data['payload'] = ipayload
	
	values = urllib.urlencode(data)
	req = 'http://' + url + '/' + server + '?' + values
	print req
	try: 
		response = urllib2.urlopen(req)
		the_page = response.read()
		print 'Message to ' + itopic + ': ' + the_page
		evaluateAction(the_page)
	except urllib2.URLError as e:
		print e.reason
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
	f.write(datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")+" ")
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
		f.write(datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")+" ")
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
    out_msg.number_of_step = abs(steps)
    out_msg.step_size = out_msg.StepSize.Value("FULL_STEP")
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["publish_topic"]["stepper"]["global"]
    topic['local'] = configuration["publish_topic"]["stepper"]["local"]
    topic['client_id'] = configuration["publish_topic"]["stepper"]["client_id"]
    topic['stream_index'] = 0
    ioant.publish(out_msg, topic)
#=====================================================
def publishEnergyMsg(value):
    msg = "Publish energy message: "+str(value)
    print msg
    
    configuration = ioant.get_configuration()
    out_msg = ioant.create_message("Temperature")
    out_msg.value = value
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["publish_topic"]["energy"]["global"]
    topic['local'] = configuration["publish_topic"]["energy"]["local"]
    topic['client_id'] = configuration["publish_topic"]["energy"]["client_id"]
    topic['stream_index'] = 0
    ioant.publish(out_msg, topic)
#=====================================================
def publishExtreme(value):
    msg = "Publish extreme message: "+str(value)
    print msg
    
    configuration = ioant.get_configuration()
    out_msg = ioant.create_message("Temperature")
    out_msg.value = value
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["publish_topic"]["extreme"]["global"]
    topic['local'] = configuration["publish_topic"]["extreme"]["local"]
    topic['client_id'] = configuration["publish_topic"]["extreme"]["client_id"]
    topic['stream_index'] = 0
    ioant.publish(out_msg, topic)
#=====================================================
def publishWanted(value):
    msg = "Publish wanted temperature message: "+str(value)
    print msg
    
    configuration = ioant.get_configuration()
    out_msg = ioant.create_message("Temperature")
    out_msg.value = value
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["publish_topic"]["wanted"]["global"]
    topic['local'] = configuration["publish_topic"]["wanted"]["local"]
    topic['client_id'] = configuration["publish_topic"]["wanted"]["client_id"]
    topic['stream_index'] = 0
    ioant.publish(out_msg, topic)
#=====================================================
def publishInertia(value):
    msg = "Publish inertia: "+str(value)
    print msg
    
    configuration = ioant.get_configuration()
    out_msg = ioant.create_message("Temperature")
    out_msg.value = value
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["publish_topic"]["x_inertia"]["global"]
    topic['local'] = configuration["publish_topic"]["x_inertia"]["local"]
    topic['client_id'] = configuration["publish_topic"]["x_inertia"]["client_id"]
    topic['stream_index'] = 0
    ioant.publish(out_msg, topic)
#=====================================================
def publishFrequence(value):
    msg = "Publish frequency message: "+str(value)
    print msg
    
    configuration = ioant.get_configuration()
    out_msg = ioant.create_message("Temperature")
    out_msg.value = value
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["publish_topic"]["frequence"]["global"]
    topic['local'] = configuration["publish_topic"]["frequence"]["local"]
    topic['client_id'] = configuration["publish_topic"]["frequence"]["client_id"]
    topic['stream_index'] = 0
    ioant.publish(out_msg, topic)
#=====================================================
def publishState(value):
    msg = "Publish state message: "+str(value)
    print msg
    
    configuration = ioant.get_configuration()
    out_msg = ioant.create_message("Temperature")
    out_msg.value = value
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["publish_topic"]["state"]["global"]
    topic['local'] = configuration["publish_topic"]["state"]["local"]
    topic['client_id'] = configuration["publish_topic"]["state"]["client_id"]
    topic['stream_index'] = 0
    ioant.publish(out_msg, topic)
#=====================================================
def publishMode(value):
    msg = "Publish mode message: "+str(value)
    print msg
    
    configuration = ioant.get_configuration()
    out_msg = ioant.create_message("Temperature")
    out_msg.value = value
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["publish_topic"]["mode"]["global"]
    topic['local'] = configuration["publish_topic"]["mode"]["local"]
    topic['client_id'] = configuration["publish_topic"]["mode"]["client_id"]
    topic['stream_index'] = 0
    ioant.publish(out_msg, topic)
#=====================================================
def publishOnOff(value):
    msg = "Publish OnOff message: "+str(value)
    print msg
    
    configuration = ioant.get_configuration()
    out_msg = ioant.create_message("Temperature")
    out_msg.value = value
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["publish_topic"]["onofftime"]["global"]
    topic['local'] = configuration["publish_topic"]["onofftime"]["local"]
    topic['client_id'] = configuration["publish_topic"]["onofftime"]["client_id"]
    topic['stream_index'] = 0
    ioant.publish(out_msg, topic)
#=====================================================
def publishStep(value):
    msg = "Publish Steps message: "+str(value)
    print msg
    
    configuration = ioant.get_configuration()
    out_msg = ioant.create_message("Temperature")
    out_msg.value = value
    topic = ioant.get_topic_structure()
    topic['top'] = 'live'
    topic['global'] = configuration["publish_topic"]["steps"]["global"]
    topic['local'] = configuration["publish_topic"]["steps"]["local"]
    topic['client_id'] = configuration["publish_topic"]["steps"]["client_id"]
    topic['stream_index'] = 0
    ioant.publish(out_msg, topic)
#==========================================
#=====================================================
def show_state_mode(st,mo):
	if st == STATE_INIT:
		print "STATE_INIT"
	if st == STATE_OFF:
		print "STATE_OFF"
	if st == STATE_WARMING:
		print "STATE_WARMING"
	if st == STATE_ON:
		print "STATE_ON"
	if mo == MODE_OFFLINE:
		print "MODE_OFFLINE"
	if mo == MODE_ONLINE:
		print "MODE_ONLINE"
#=====================================================
def show_action_bit_info(a):
	
	message = "action " + str(a)
	c = a & 1
	if c == 1:
		message += "- inertia active "
	c = a & 2
	if c == 2:
		message +=  "- heater is off "
	c = a & 4
	if c == 4:
		message +=  "- no warming above 20 "
	c = a & 8
	if c == 8:
		message +=  "- no cooling possible "
	c = a & 16
	if c == 16:
		message +=  "- below min steps "
	c = a & 32
	if c == 32:
		message +=  "- steps is 0 "
	c = a & 64
	if c == 64:
		message +=  "- energy limit reached "
	c = a & 128
	if c == 128:
		message +=  "- 128 no defined "
	print message
	write_history(message)
#=====================================================
def heater_model():
	global g_minsteps,g_maxsteps,g_defsteps
	global g_minsmoke
	global g_mintemp,g_maxtemp
	global g_minheat,g_maxheat
	global g_x_0,g_y_0
	global g_relax
	global r_inertia
	global g_max_energy
	global g_current_position
	global r_uptime
	global g_state
	global g_mode
	global g_inertia
	global g_uptime
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
	global temp_smoke_ave
	global g_period
	global g_counter
	global STATE_INIT
	global STATE_OFF
	global STATE_WARMING
	global STATE_ON
	global MODE_OFFLINE
	global MODE_ONLINE
	
	publishInertia(r_inertia)
	publishState(g_state)
	publishMode(g_mode)
	if r_uptime < g_uptime:
		publishOnOff(r_uptime)

	CLOCKWISE = 0 # decrease
	COUNTERCLOCKWISE = 1 # increase

	coeff1 = (g_maxheat - g_y_0)/(g_mintemp - g_x_0)
	mconst1 = g_y_0 - coeff1*g_x_0
	coeff2 = (g_y_0 - g_minheat)/(g_x_0 - g_maxtemp)
	mconst2 = g_minheat - coeff2*g_maxtemp

	y = 999
	energy = 999
	steps = 999
	all_data_is_new = 0
	old_data = 0
	action = 0

	# If necessary data not available: do nothing
	ndi = 0
	if temperature_outdoor == 999:
		message = "No data - temperature_outdoor"
		write_log(message)
		#write_history(message)
		ndi = ndi + 1

	if temperature_water_out == 999:
		message = "No data - temperature_water_out"
		write_log(message)
		#write_history(message)
		ndi = ndi + 1

	if temperature_water_in == 999:
		message = "No data - temperature_water_in"
		write_log(message)
		#write_history(message)
		ndi = ndi + 1

	if temperature_smoke == 999:
		message = "No data - temperature_smoke"
		write_log(message)
		#write_history(message)
		ndi = ndi + 1

	if ndi > 0:
		print ndi
	if ndi == 0:
		all_data_is_available = 1
	else:
		all_data_is_available = 0

	old_data = 0

	timeout_temperature_indoor -= 1
	timeout_temperature_outdoor -= 1
	timeout_temperature_water_in -= 1
	timeout_temperature_water_out -= 1
	timeout_temperature_smoke -= 1

	if timeout_temperature_indoor < 1:
		message = "Old data - temperature_indoor " + str(timeout_temperature_indoor)
		write_log(message)
		write_history(message)
		old_data= 1
	if timeout_temperature_outdoor < 1:
		message = "Old data - temperature_outdoor " + str(timeout_temperature_outdoor)
		write_log(message)
		write_history(message)
		old_data= 1
	if timeout_temperature_water_in < 1:
		message = "Old data - temperature_water_in " + str(timeout_temperature_water_in)
		write_log(message)
		write_history(message)
		old_data= 1

	if timeout_temperature_water_out < 1:
		message = "Old data - temperature_water_out " + str(timeout_temperature_water_out)
		write_log(message)
		write_history(message)
		old_data= 1
	if timeout_temperature_smoke < 1:
		message = "Old data - temperature_smoke " + str(timeout_temperature_smoke)
		write_log(message)
		write_history(message)
		old_data= 1


	if g_mode == MODE_OFFLINE:
		if all_data_is_available == 1:
			g_mode = MODE_ONLINE
			write_log("MODE_OFFLINE -> MODE_ONLINE")
			r_inertia = g_inertia
	if g_mode == MODE_ONLINE:
		old_data = 0
		if old_data == 1:
			g_mode = MODE_OFFLINE
			write_log("MODE_ONLINE -> MODE_OFFLINE")
		if g_state == STATE_OFF:
			r_uptime -= 1
			if r_uptime < 0:
				r_uptime = 0
			if temperature_smoke > g_minsmoke:
				g_state = STATE_WARMING
				write_log("STATE_OFF -> STATE_WARMING")
		if g_state == STATE_WARMING:
			r_uptime += 1
			if r_uptime == g_uptime:
				g_state = STATE_ON
				write_log("STATE_WARMING -> STATE_ON")
			if temp_smoke_ave < g_minsmoke:
				g_state = STATE_OFF
				write_log("STATE_WARMING -> STATE_OFF")
				r_uptime = 0
		if g_state == STATE_ON:
			action = 0
			if r_inertia > 0: # delay after latest order
				r_inertia -= 1
				action += 1
			if temp_smoke_ave < g_minsmoke: # heater is off
				action += 2
				g_state = STATE_OFF
				write_log("STATE_ON -> STATE_OFF")
				r_uptime = 0
			if temperature_indoor > 20: # no warming above 20
				action += 4
			if temperature_water_in > temperature_water_out: # no cooling
				action += 8

			temp = temperature_outdoor

			if temp > g_maxtemp:
				temp = g_maxtemp
			if temp < g_mintemp:
				temp = g_mintemp

			if temp < g_x_0:
				y = coeff1*temp + mconst1
			else:
				y = coeff2*temp + mconst2

			publishWanted(y)
			steps = round((y - temperature_water_out)*g_relax)
			print "g_relax = " + str(g_relax)
			print "steps = " + str(steps)
			print "temperature_water_out = " + str(temperature_water_out)
			publishStep(steps)
			if abs(steps) < g_minsteps: # min steps
				action += 16

			energy = temperature_water_out - temperature_water_in
			if energy > g_max_energy and steps > 0:
				action += 64

			if steps > 0:
				direction = COUNTERCLOCKWISE
			if steps < 0:
				direction = CLOCKWISE
			if steps == 0:
				action += 32

			if steps > g_maxsteps:
				steps = g_maxsteps
				
			#show_action_bit_info(action)
			
			if action == 0:
				publishStepperMsg(int(steps), direction)
				print ">>>>>> Move Stepper " + str(steps) + " " + str(direction)
				r_inertia = g_inertia
				if direction == COUNTERCLOCKWISE:
					g_current_position += steps
				if direction == CLOCKWISE:
					g_current_position -= steps
#========================================================================
	show_state_mode(g_state,g_mode)
   	if energy < 999:
		publishEnergyMsg(energy)
	status = "Uptime=" + str(r_uptime) + " target=" + str(y) + "("+str(temperature_water_out)+")" + " inertia " + str(r_inertia) + " steps " + str(steps)
	status = status + " Pos=" + str(g_current_position) + " indoor " + str(timeout_temperature_indoor) + " outdoor " + str(timeout_temperature_outdoor)
	print status
	payload = '{"flags" : "' + str(action) + '}'
	publishGowData( payload, g_counter )
	
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
def find_extreme(x1,x2,x3):
	global tmax,tmin
	t = datetime.datetime.now() 
	print "min-max: " + str(x1) + " " + str(x2) + " " + str(x3)
	if x1 > x2 and x2 > x3:
		print "values falling"
	if x1 < x2 and x2 < x3:
		print "values rising"
	if x1 >= x2 and x2 < x3: # minimum
		d = t - tmin
		f = d.seconds
		tmin = t
		publishFrequence(f)
		publishExtreme(1)
	if x1 <= x2 and x2 > x3: # maximum
		d = t - tmax
		f = d.seconds
		tmax = t
		publishFrequence(f)
		publishExtreme(2)	
#=====================================================
def setup(configuration):
	global v1,v2,v3
	v1 = 30.0
	v2 = 30.0
	v3 = 30.0
	global tmin,tmax
	tmin = datetime.datetime.now() 
	tmax = datetime.datetime.now() 
    # Configuration
	global g_minsteps,g_maxsteps,g_defsteps
	global g_minsmoke,g_max_energy
	global g_mintemp,g_maxtemp
	global g_minheat,g_maxheat
	global g_x_0,g_y_0
	global g_uptime
	global g_relax
	global r_inertia
	global g_current_position
	global r_uptime
	global g_state
	global g_mode
	global g_inertia
	global STATE_INIT
	global STATE_OFF
	global STATE_WARMING
	global STATE_ON
	global MODE_OFFLINE
	global MODE_ONLINE
	global g_counter

	g_counter = 0
	STATE_INIT = 0
	STATE_OFF = 1
	STATE_WARMING = 2
	STATE_ON = 3
	MODE_OFFLINE = 1
	MODE_ONLINE = 2
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
	g_relax = 3.0
	g_max_energy = 4.0
	g_period = 5000
	g_gow_server = 'gow.test.com'
	g_gow_topic = 'etc/etc/etc/0'
	g_current_position = read_position()
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
	g_period   = int(configuration["ioant"]["communication_delay"])
	g_period   = round(g_period/1000)
	g_gow_server = str(configuration["gow_server"])
	g_gow_topic = str(configuration["gow_topic"])
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
	g_uptime = int(configuration["algorithm"]["onofftime"])
	g_inertia = int(configuration["algorithm"]["inertia"])
	g_relax = float(configuration["algorithm"]["relax"])
	g_max_energy = float(configuration["algorithm"]["maxenergy"])

	g_state = STATE_OFF
	write_log("START -> STATE_OFF")
	g_mode = MODE_OFFLINE
	write_log("START -> MODE_OFFLINE")
	r_inertia = g_inertia
	r_uptime = g_uptime

	init_log()
	init_history()

#=====================================================
def loop():
    global r_inertia
    global g_counter
    ioant.update_loop()
    g_counter += 1
    if g_counter > 999999:
	g_counter = 0
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
	global v1,v2,v3,temp_smoke_ave
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
			v1 = v2
			v2 = v3
			v3 = temperature_smoke
			temp_smoke_ave = (v1 + v2 + v3)/3
			find_extreme(v1,v2,v3)

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
