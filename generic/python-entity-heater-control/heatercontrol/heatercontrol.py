# =============================================
# File: heatercontrol.py
# Author: Benny Saxen
# Date: 2019-02-03
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
#======================================
class Twin:
   # state
   r_state   = 0
   r_mode    = 0
   r_inertia = 0
   r_onoff   = 0
   r_counter = 0

   g_inertia = 0
   g_onoff   = 0
   g_period  = 0

   STATE_INIT    = 0
   STATE_OFF     = 1
   STATE_WARMING = 2
   STATE_ON      = 3

   MODE_OFFLINE  = 1
   MODE_ONLINE   = 2

   # Subscriptions
   temperature_indoor    = 0.0
   temperature_outdoor   = 0.0
   temperature_water_in  = 0.0
   temperature_water_out = 0.0
   temperature_smoke     = 0.0
   temp_smoke_ave        = 0.0
   v1 = 0.0
   v2 = 0.0
   v3 = 0.0

   hash_indoor    = 0
   hash_outdoor   = 0
   hash_water_in  = 0
   hash_water_out = 0
   hash_smoke     = 0

   timeout_temperature_indoor    = 60
   timeout_temperature_outdoor   = 60
   timeout_temperature_water_in  = 60
   timeout_temperature_water_out = 60
   timeout_temperature_smoke     = 60

   # algorithm configuration
   g_mintemp = 0.0
   g_maxtemp = 0.0
   g_minheat = 0.0
   g_maxheat = 0.0
   g_x_0     = 0.0
   g_y_0     = 0.0
   g_relax   = 4.0
   g_min_smoke = 0.0
   g_minsteps  = 0
   g_maxsteps  = 0
   g_defsteps  = 0  
   g_max_energy = 0 
 
   # other
   g_tmax = 0
   g_tmin = 0

   # gow
   g_gow_server = 'test.com'
   g_gow_topic  = 'test/topic'
#======================================
s1 = Twin()

#===================================================
def publishGowStatic(p1):
#===================================================
	url = p1.g_gow_server
	server = 'gowServer.php'
	data = {}
	# meta data
	data['do']       = 'stat'
	data['topic']    = p1.g_gow_topic
	data['no']       = p1.r_counter
	data['wrap']     = 999999
	data['period']   = p1.g_period
	data['platform'] = 'python'
	data['url']      = p1.g_gow_server
  	data['ssid']     = 'nowifi'
	data['action']   = 1
	
	values = urllib.urlencode(data)
	req = 'http://' + url + '/' + server + '?' + values
	print req
	try: 
		response = urllib2.urlopen(req)
		the_page = response.read()
		print 'Message to ' + p1.g_gow_topic + ': ' + the_page
		#evaluateAction(the_page)
	except urllib2.URLError as e:
		print e.reason
#===================================================
def publishGowDynamic(p1, ipayload):
#===================================================
	url = p1.g_gow_server
	server = 'gowServer.php'
	data = {}
	# meta data
	data['do']       = 'dyn'
	data['topic']    = p1.g_gow_topic
	data['no']       = p1.r_counter
	data['rssi']     = 0
	data['dev_ts']   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	data['fail']     = 0
	# payload
	data['payload'] = ipayload
	
	values = urllib.urlencode(data)
	req = 'http://' + url + '/' + server + '?' + values
	print req
	try: 
		response = urllib2.urlopen(req)
		the_page = response.read()
		print 'Message to ' + p1.g_gow_topic + ': ' + the_page
		#evaluateAction(the_page)
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
#=====================================================
def show_state_mode(p1):
	if p1.r_state == p1.STATE_INIT:
		print "STATE_INIT"
	if p1.r_state == p1.STATE_OFF:
		print "STATE_OFF"
	if p1.r_state == p1.STATE_WARMING:
		print "STATE_WARMING"
	if p1.r_state == p1.STATE_ON:
		print "STATE_ON"
	if p1.r_mode == p1.MODE_OFFLINE:
		print "MODE_OFFLINE"
	if p1.r_mode == p1.MODE_ONLINE:
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
def heater_model(p1):	
	publishInertia(p1.r_inertia)
	publishState(p1.r_state)
	publishMode(p1.r_mode)
	if p1.r_onoff < p1.g_onoff:
		publishOnOff(p1.r_onoff)

	CLOCKWISE = 0 # decrease
	COUNTERCLOCKWISE = 1 # increase

	coeff1 = (p1.g_maxheat - p1.g_y_0)/(p1.g_mintemp - p1.g_x_0)
	mconst1 = p1.g_y_0 - coeff1*p1.g_x_0
	coeff2 = (p1.g_y_0 - p1.g_minheat)/(p1.g_x_0 - p1.g_maxtemp)
	mconst2 = p1.g_minheat - coeff2*p1.g_maxtemp

	y = 999
	energy = 999
	steps = 999
	all_data_is_new = 0
	old_data = 0
	action = 0

	# If necessary data not available: do nothing
	ndi = 0
	if p1.temperature_outdoor == 999:
		message = "No data - temperature_outdoor"
		write_log(message)
		#write_history(message)
		ndi = ndi + 1

	if p1.temperature_water_out == 999:
		message = "No data - temperature_water_out"
		write_log(message)
		#write_history(message)
		ndi = ndi + 1

	if p1.temperature_water_in == 999:
		message = "No data - temperature_water_in"
		write_log(message)
		#write_history(message)
		ndi = ndi + 1

	if p1.temperature_smoke == 999:
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

	p1.timeout_temperature_indoor -= 1
	p1.timeout_temperature_outdoor -= 1
	p1.timeout_temperature_water_in -= 1
	p1.timeout_temperature_water_out -= 1
	p1.timeout_temperature_smoke -= 1

	if p1.timeout_temperature_indoor < 1:
		message = "Old data - temperature_indoor " + str(p1.timeout_temperature_indoor)
		write_log(message)
		write_history(message)
		old_data= 1
	if p1.timeout_temperature_outdoor < 1:
		message = "Old data - temperature_outdoor " + str(p1.timeout_temperature_outdoor)
		write_log(message)
		write_history(message)
		old_data= 1
	if p1.timeout_temperature_water_in < 1:
		message = "Old data - temperature_water_in " + str(p1.timeout_temperature_water_in)
		write_log(message)
		write_history(message)
		old_data= 1

	if p1.timeout_temperature_water_out < 1:
		message = "Old data - temperature_water_out " + str(p1.timeout_temperature_water_out)
		write_log(message)
		write_history(message)
		old_data= 1
	if p1.timeout_temperature_smoke < 1:
		message = "Old data - temperature_smoke " + str(p1.timeout_temperature_smoke)
		write_log(message)
		write_history(message)
		old_data= 1


	if p1.r_mode == p1.MODE_OFFLINE:
		if all_data_is_available == 1 and old_data == 0:
			p1.r_mode = p1.MODE_ONLINE
			write_log("MODE_OFFLINE -> MODE_ONLINE")
			p1.r_inertia = p1.g_inertia
	if p1.r_mode == p1.MODE_ONLINE:
		if old_data == 1:
			p1.r_mode = p1.MODE_OFFLINE
			write_log("MODE_ONLINE -> MODE_OFFLINE")
		if p1.r_state == p1.STATE_OFF:
			p1.r_onoff -= 1
			if p1.r_onoff < 0:
				p1.r_onoff = 0
			if p1.temperature_smoke > p1.g_minsmoke:
				p1.r_state = p1.STATE_WARMING
				write_log("STATE_OFF -> STATE_WARMING")
		if p1.r_state == p1.STATE_WARMING:
			p1.r_onoff += 1
			if p1.r_onoff == p1.g_onoff:
				p1.r_state = p1.STATE_ON
				write_log("STATE_WARMING -> STATE_ON")
			if p1.temp_smoke_ave < p1.g_minsmoke:
				p1.r_state = p1.STATE_OFF
				write_log("STATE_WARMING -> STATE_OFF")
				p1.r_onoff = 0
		if p1.r_state == p1.STATE_ON:
			action = 0
			if p1.r_inertia > 0: # delay after latest order
				p1.r_inertia -= 1
				action += 1
			if p1.temp_smoke_ave < p1.g_minsmoke: # heater is off
				action += 2
				p1.r_state = p1.STATE_OFF
				write_log("STATE_ON -> STATE_OFF")
				p1.r_onoff = 0
			if p1.temperature_indoor > 20: # no warming above 20
				action += 4
			if p1.temperature_water_in > p1.temperature_water_out: # no cooling
				action += 8

			temp = p1.temperature_outdoor

			if temp > p1.g_maxtemp:
				temp = p1.g_maxtemp
			if temp < p1.g_mintemp:
				temp = p1.g_mintemp

			if temp < p1.g_x_0:
				y = coeff1*temp + mconst1
			else:
				y = coeff2*temp + mconst2

			publishWanted(y)
			tmp1 = y*p1.g_relax
			tmp2 = p1.temperature_water_out*p1.g_relax
			tmp3 = tmp1 - tmp2
			steps = round(tmp3)
			publishFrequence(p1.temperature_water_out)
			print "tmp1=" + str(tmp1) + " tmp2="+str(tmp2) + " tmp3=" + str(tmp3)
			print "g_relax = " + str(p1.g_relax)
			print "steps = " + str(steps)
			print "temperature_water_out = " + str(p1.temperature_water_out)
			publishStep(steps)
			if abs(steps) < p1.g_minsteps: # min steps
				action += 16

			energy = p1.temperature_water_out - p1.temperature_water_in
			if energy > p1.g_max_energy and steps > 0:
				action += 64

			if steps > 0:
				direction = COUNTERCLOCKWISE
			if steps < 0:
				direction = CLOCKWISE
			if steps == 0:
				action += 32

			if steps > p1.g_maxsteps:
				steps = p1.g_maxsteps
				
			#show_action_bit_info(action)
			
			if action == 0:
				publishStepperMsg(int(steps), direction)
				print ">>>>>> Move Stepper " + str(steps) + " " + str(direction)
				p1.r_inertia = p1.g_inertia
#========================================================================
	show_state_mode(p1)
   	if energy < 999:
		publishEnergyMsg(energy)

	payload  = '{\n'
	payload += '"flags" : "' + str(action) + '",\n'
	payload += '"steps" : "' + str(steps) + '",\n'
	payload += '"target" : "' + str(y) + '",\n'
	payload += '"mode" : "' + str(p1.r_mode) + '",\n'
	payload += '"state" : "' + str(p1.r_state) + '",\n'
	payload += '"inertia" : "' + str(p1.r_inertia) + '",\n'
	payload += '"onoff" : "' + str(p1.r_onoff) + '",\n'
	payload += '"temperature_water_out" : "' + str(p1.temperature_water_out) + '",\n'
	payload += '"temperature_water_in" : "' + str(p1.temperature_water_in) + '",\n'
	payload += '"temperature_smoke" : "' + str(p1.temperature_smoke) + '"\n'
	payload += '}\n'
	publishGowDynamic( p1, payload)
	
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
def find_extreme(p1):
	t = datetime.datetime.now() 
	print "min-max: " + str(p1.v1) + " " + str(p1.v2) + " " + str(p1.v3)
	if p1.v1 > p1.v2 and p1.v2 > p1.v3:
		print "values falling"
	if p1.v1 < p1.v2 and p1.v2 < p1.v3:
		print "values rising"
	if p1.v1 >= p1.v2 and p1.v2 < p1.v3: # minimum
		d = t - p1.tmin
		f = d.seconds
		p1.tmin = t
		#publishFrequence(f)
		publishExtreme(1)
	if p1.v1 <= p1.v2 and p1.v2 > p1.v3: # maximum
		d = t - p1.tmax
		f = d.seconds
		p1.tmax = t
		#publishFrequence(f)
		publishExtreme(2)	
#=====================================================
def setup(configuration):
	global s1

	s1.v1 = 30.0
	s1.v2 = 30.0
	s1.v3 = 30.0

	s1.tmin = datetime.datetime.now() 
	s1.tmax = datetime.datetime.now() 

	s1.r_counter = 0
	
	s1.STATE_INIT = 0
	s1.STATE_OFF = 1
	s1.STATE_WARMING = 2
	s1.STATE_ON = 3
	s1.MODE_OFFLINE = 1
	s1.MODE_ONLINE = 2
	
	s1.g_minsteps = 5
	s1.g_maxsteps = 30
	s1.g_defsteps = 10
	s1.g_minsmoke = 27
	s1.g_mintemp = -7
	s1.g_maxtemp = 10
	s1.g_minheat = 20
	s1.g_maxheat = 40
	
	s1.g_x_0 = 0
	s1.g_y_0 = 35
	s1.g_relax = 3.0
	s1.g_max_energy = 4.0
	s1.g_period = 5000
	s1.g_gow_server = 'gow.test.com'
	s1.g_gow_topic = 'etc/etc/etc/0'

	s1.temperature_indoor    = 999
	s1.temperature_outdoor   = 999
	s1.temperature_water_in  = 999
	s1.temperature_water_out = 999
	s1.temperature_smoke     = 999

	s1.timeout_temperature_indoor = 60
	s1.timeout_temperature_outdoor = 60
	s1.timeout_temperature_water_in = 60
	s1.timeout_temperature_water_out = 60
	s1.timeout_temperature_smoke = 60
	
	ioant.setup(configuration)
	configuration = ioant.get_configuration()
	tempv   = int(configuration["ioant"]["communication_delay"])
	s1.g_period   = round(tempv/1000)
	s1.g_gow_server = str(configuration["gow_server"])
	s1.g_gow_topic = str(configuration["gow_topic"])
	s1.g_minsteps = int(configuration["algorithm"]["minsteps"])
	s1.g_maxsteps = int(configuration["algorithm"]["maxsteps"])
	s1.g_defsteps = int(configuration["algorithm"]["defsteps"])
	s1.g_minsmoke = float(configuration["algorithm"]["minsmoke"])
	s1.g_mintemp = float(configuration["algorithm"]["mintemp"])
	s1.g_maxtemp = float(configuration["algorithm"]["maxtemp"])
	s1.g_minheat = float(configuration["algorithm"]["minheat"])
	s1.g_maxheat = float(configuration["algorithm"]["maxheat"])
	s1.g_x_0 = float(configuration["algorithm"]["x_0"])
	s1.g_y_0 = float(configuration["algorithm"]["y_0"])
	s1.g_onoff = int(configuration["algorithm"]["onofftime"])
	s1.g_inertia = int(configuration["algorithm"]["inertia"])
	s1.g_relax = float(configuration["algorithm"]["relax"])
	s1.g_max_energy = float(configuration["algorithm"]["maxenergy"])

	s1.r_state = s1.STATE_OFF
	write_log("START -> STATE_OFF")
	s1.r_mode = s1.MODE_OFFLINE
	write_log("START -> MODE_OFFLINE")
	s1.r_inertia = s1.g_inertia
	s1.r_onoff = s1.g_onoff

	init_log()
	init_history()
	publishGowStatic(s1)
#=====================================================
def loop():
    global s1
    ioant.update_loop()
    s1.r_counter += 1
    if s1.r_counter > 999999:
	s1.r_counter = 0
    
    mtemp = s1.r_counter % 5
    if mtemp == 0:
	heater_model(s1)

#=====================================================
def on_message(topic, message):
	global s1
	""" Message function. Handles recieved message from broker """
	if topic["message_type"] == ioant.get_message_type("Temperature"):
		shash = getTopicHash(topic)
		#logging.info("Temp = "+str(message.value)+" hash="+str(shash))
		if shash == s1.hash_indoor:
			print "===> indoor " + str(message.value)
			s1.temperature_indoor = message.value
			s1.timeout_temperature_indoor = 60
		if shash == s1.hash_outdoor:
			print "===> outdoor " + str(message.value)
			s1.temperature_outdoor = message.value
			s1.timeout_temperature_outdoor = 60
		if shash == s1.hash_water_in:
			print "===> water in " + str(message.value)
			s1.temperature_water_in = message.value
			s1.timeout_temperature_water_in = 60
		if shash == s1.hash_water_out:
			print "===> water out " + str(message.value)
			s1.temperature_water_out = message.value
			s1.timeout_temperature_water_out = 60
		if shash == s1.hash_smoke:
			print "===> smoke " + str(message.value)
			s1.temperature_smoke = message.value
			s1.timeout_temperature_smoke = 60
			s1.v1 = s1.v2
			s1.v2 = s1.v3
			s1.v3 = s1.temperature_smoke
			s1.temp_smoke_ave = (s1.v1 + s1.v2 + s1.v3)/3
			find_extreme(s1)

    #if "Temperature" == ioant.get_message_type_name(topic[message_type]):

#=====================================================
def on_connect():
    """ On connect function. Called when connected to broker """
    global s1

    # There is now a connection
    s1.hash_indoor    = subscribe_to_topic("indoor","Temperature")
    s1.hash_outdoor   = subscribe_to_topic("outdoor","Temperature")
    s1.hash_water_in  = subscribe_to_topic("water_in","Temperature")
    s1.hash_water_out = subscribe_to_topic("water_out","Temperature")
    s1.hash_smoke     = subscribe_to_topic("smoke","Temperature")

# =============================================================================
# Above this line are mandatory functions
# =============================================================================
# Mandatory line
ioant = IOAnt(on_connect, on_message)
