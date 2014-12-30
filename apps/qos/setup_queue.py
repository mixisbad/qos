#! /usr/bin/python
#  coding: utf-8

'''
Add queues to Mininet using ovs-vsctl and ovs-ofctl
@Author Pattanapoom Phinjirapong
'''

import os
import sys
import time
import subprocess

queuecmd = ""
port = ""
q_max = []
q_min = []
qos_max = ""
#qos_min = ""

i = 1
while i < len(sys.argv) :
    if sys.argv[i] == "-p":
        i = i+1
        port = sys.argv[i]
        i = i+1
    elif sys.argv[i] == "-qmax":
        i = i+1
        while (sys.argv[i][0] != '-') and (i < len(sys.argv)):
            q_max.append(sys.argv[i])
            i = i+1
    elif sys.argv[i] == "-qmin":
        i = i+1
        while (sys.argv[i][0] != '-') and (i < len(sys.argv)):
            q_min.append(sys.argv[i])
            i = i+1    
    elif sys.argv[i] == "-qosmax":
        i = i+1
        qos_max = sys.argv[i]
        i=i+1
    #else if sys.argv[i] == "-qosmin":
    #    i = i+1
    #    qos_min = sys.argv[i]
    #    i=i+1
        
queuecmd = "sudo ovs-vsctl -- set port %s qos=@defaultqos -- " % port
queuecmd = queuecmd + "--id=defaultqos create qos type=linux-htb other-config:max-rate=%s " % qos_max
for i in range(len(q_min)):
    if i == 0:
        queuecmd = queuecmd + "queues=0=@q0"
    else:
        queuecmd = queuecmd + "," + str(i) + "=@q" + str(i)
queuecmd = queuecmd + " -- "

for i in range( len(q_min)):
    if i == 0:
        queuecmd = queuecmd +     "--id=@q0 create queue other-config:max-rate=%s other-config:min-rate=%s " % (q_max[i],q_min[i])
    else:
        queuecmd = queuecmd + "-- --id=@q%s create queue other-config:max-rate=%s other-config:min-rate=%s " %(str(i),q_max[i],q_min[i])

print queuecmd
#q_res = os.popen(queuecmd).read()
