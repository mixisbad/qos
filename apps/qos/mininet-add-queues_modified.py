#! /usr/bin/python
#  coding: utf-8

'''
Add queues to Mininet using ovs-vsctl and ovs-ofctl
@Author Ryan Wallner
'''

import os
import sys
import time
import subprocess

def find_all(a_str, sub_str):
    start = 0
    b_starts = []
    while True:
        start = a_str.find(sub_str, start)
        if start == -1: return b_starts
        #print start
        b_starts.append(start)
        start += 1


if os.getuid() != 0:
    print "Root permissions required"
    exit()


cmd = "ovs-vsctl show"
p = os.popen(cmd).read()
#print p

brdgs = find_all(p, "Bridge")
#print brdgs

switches = []
for bn in brdgs:
    first_quote = bn+6
    while p[first_quote] != '"':
        first_quote = first_quote+1
    first_quote = first_quote+1
    second_quote = first_quote+1
    while p[second_quote] != '"':
        second_quote = second_quote+1
    sw =  p[first_quote:second_quote]
    switches.append(sw)

ports = find_all(p,"Port")
print ports

prts = []
for prt in ports:
    first_quote = prt+5
    while p[first_quote] != '"':
        first_quote = first_quote+1
    first_quote = first_quote+1
    second_quote = first_quote+1
    while p[second_quote] != '"':
        second_quote = second_quote+1
    prt =  p[first_quote:second_quote]
    if '-' in prt:
        prts.append(prt)
config_strings = {}
for i in range(len(switches)):
    str = ""
    sw = switches[i]
    for n in range(len(prts)):
        #verify correct order
        if switches[i] == prts[n][0:prts[n].find("-")]:
            port_name = prts[n]
            str = str+" -- set port %s qos=@defaultqos" % port_name
    config_strings[sw] = str

#build queues per sw
#print config_strings
for sw in switches:
    queuecmd = "sudo ovs-vsctl %s -- --id=@defaultqos " % config_strings[sw]
    queuecmd = queuecmd + "create qos type=linux-htb other-config:max-rate=3000000 queues=0=@q0,1=@q1,2=@q2 -- "
    queuecmd = queuecmd + "--id=@q0 create queue other-config:max-rate=3000000 -- "
    queuecmd = queuecmd + "--id=@q1 create queue other-config:max-rate=2000000 -- "
    queuecmd = queuecmd + "--id=@q2 create queue other-config:max-rate=2000000 other-config:min-rate=2000000"
    q_res = os.popen(queuecmd).read()
    print q_res




