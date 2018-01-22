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
buf = []
bufSize = 86400
freq = []

trans = []
index = []
sumint = []
mx = []
#======================================================================
def dec_to_bin(x):
    return str(bin(x)[2:])
#======================================================================
def bubbleAsc(listA,listB):
    length = len(listA) - 1
    sorted = False

    while not sorted:
        sorted = True
        for i in range(length):
            if listA[i] > listA[i+1]:
                sorted = False
                listA[i], listA[i+1] = listA[i+1], listA[i]
                listB[i], listB[i+1] = listB[i+1], listB[i]
#======================================================================
def bubbleDesc(listA,listB):
    length = len(listA) - 1
    sorted = False

    while not sorted:
        sorted = True
        for i in range(length):
            if listA[i] > listA[i-1]:
                sorted = False
                listA[i], listA[i-1] = listA[i-1], listA[i]
                listB[i], listB[i-1] = listB[i-1], listB[i]
#======================================================================
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
#======================================================================
def addCircBuf(value):
    print "add to buffer"
    global buf
    global bufSize
    try:
        file = open("buffer.work", "r")
    except IOError:
        file = open("buffer.work", "w")
        for i in range(0,bufSize):
            file.write("%d\n" % (buf[i]))
        file.close()
        print "Buffer initiated"

    file = open("buffer.work", "r")
    i = 0
    for line in file:
        buf[i] = int(line)
        i = i + 1
    file.close()

    file = open("buffer.work", "w")
    for i in range(1,bufSize):
        file.write("%d\n" % (buf[i]))
        #print ("%d %d" % (i,buf[i]))
    file.write("%d\n" % (int(value)))
    file.close()
#======================================================================
def calcDevices():
    global buf,freq,trans,index,sumint,mx
    global bufSize

    fmax = 0

    for i in range(0,9000):
        freq[i] = 0

    for i in range(0,bufSize):
        ix = int(buf[i]/100)
        if ix > 0:
            freq[ix] += 1
            if fmax < ix:
                fmax = ix

    file = open("freq.work", "w")
    for i in range(1,fmax+1):
        if freq[i] != 0:
            file.write("%d %d\n" % (i,freq[i]))
            #print "."*freq[i]
            #print i
    file.close()
#-----------------------------------
    for n_devices in range(1,12):
#-----------------------------------
# Init
        tmax = 0

        for i in range(0,9000):
            trans[i] = 0
            index[i] = 0
            sumint[i] = 0
            mx[i] = 0

        for i in range(1,bufSize):
            old = int(buf[i-1])
            value  = int(buf[i])
            ix = abs(int(value) - old)
            ix = int(ix/100)
            if ix > 0:
                trans[ix] += 1 # number of transitions
                index[ix] = ix # power interval
                if tmax < ix:
                    tmax = ix

        file = open("trans.work", "w")
        for i in range(1,tmax+1):
            file.write("%d %d\n" % (index[i],trans[i]))
        file.close()

        bubbleDesc(trans,index)

        file = open("trans_sorted.work", "w")
        for i in range(1,tmax+1):
            file.write("%d %d\n" % (index[i],trans[i]))
        file.close()

        for k in range(n_devices):
            print ("Device %d %d" % (k,index[k]))
            #print "================"
        for i in range(2**n_devices):
            bb = dec_to_bin(i)
            sumint[i] = 0
            for j in range(len(bb)):
                if bb[j] == '1':
                    sumint[i] = sumint[i] + int(index[len(bb)-j-1])
            mx[sumint[i]] = 1


        tot = 0
        i = 0
        hit = 0
        for j in range(1,fmax+1):
            power = index[j]
            freqv  = freq[j]
            hit = hit + mx[power]*freqv
            tot = tot + freqv

    #print ("%d tot=%d hit=%d" % (n_devices,tot,hit))
        if tot > 0:
            ftemp =  float(hit)/float(tot)
            print ("====> %d %f tot=%f hit=%f" % (n_devices,ftemp,tot,hit))
#======================================================================
def setup(configuration):
    global buf,freq
    global bufSize

    for i in range(0,bufSize):
        buf.append(0)
        freq.append(0)
        trans.append(0)

    for i in range(0,9000):
        index.append(0)
        sumint.append(0)
        mx.append(0)

    """ setup function """
    ioant.setup(configuration)
#======================================================================
def loop():
    """ Loop function """
    ioant.update_loop()
#======================================================================
def on_message(topic, message):
    global prev_value
    global new_value
    global ackum
    prev_value = new_value
    new_value = message.value
    print "----------------"
    print new_value
    addCircBuf(new_value)
    calcDevices()
    #if prev_value > 0.0:
        #delta = prev_value - new_value
        #ackum = ackum + delta
        #print delta
        #print ackum
#======================================================================
def on_connect():
    """ On connect function. Called when connected to broker """
    subscribe_to_topic("ElectricPower")

# =============================================================================
# Above this line are mandatory functions
# =============================================================================
# Mandatory line
ioant = IOAnt(on_connect, on_message)
