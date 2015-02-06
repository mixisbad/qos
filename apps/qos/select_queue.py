#! /usr/bin/python
#  coding: utf-8

import sys
import os

server_nodes = {}

topo_detail = open('topology_detail.txt','r')
line = topo_detail.readline()
item = line.split()

#start mapping nodes
while len(item) == 0 or item[0] != 'node':
    line = topo_detail.readline()
    item = line.split()


line = topo_detail.readline()
print "line : " + line
item = line.split()
while len(item) > 0:
    #found server
    if "." in item[1]:
        print "found server"
        print item[0] + " " + item[1] + " " + item[2]
        server_dict = {}
        server_dict['name'] = item[0]
        server_dict['queue'] = item[2]
        #use ip as a key in server_nodes
        server_nodes[item[1]] = server_dict

    line = topo_detail.readline()
    print "line : " + line
    item = line.split()

#all servers are in server_nodes
print "num of argv : " + str(len(sys.argv))
print sys.argv

if len(sys.argv) > 1:
    controller_ip = sys.argv[1]
    host_ip = sys.argv[2]
    server_ip = sys.argv[3]
    mode = sys.argv[4]
    name = sys.argv[5]
    name_fw = name + "-f"
    name_bw = name + "-b"
    if mode == 'add':
        server_info = server_nodes[server_ip]
        queue_id = server_info['queue']

        #add route from src to dst
        os.system('./qospath2.py -a -N "%s" -c %s -S %s -D %s -J ' % (name_fw,controller_ip,host_ip,server_ip)  + "'" + '{"eth-type":"0x0800","protocol":"6","queue":"%s"}' % queue_id + "'")
        #add route from dst back to src
        os.system('./qospath2.py -a -N "%s" -c %s -S %s -D %s -J ' % (name_bw,controller_ip,server_ip,host_ip)  + "'" + '{"eth-type":"0x0800","protocol":"6","queue":"%s"}' % queue_id + "'")

        #print './qospath2.py -a -N "%s" -c %s -S %s -D %s -J ' % (name,controller_ip,host_ip,server_ip)  + "'" + '{"eth-type":"0x0800","protocol":"6","queue":"%s"}' % queue_id + "'"

        #print './qospath2.py -a -N "%s" -c %s -S %s -D %s -J ' % (name,controller_ip,server_ip,host_ip)  + "'" + '{"eth-type":"0x0800","protocol":"6","queue":"%s"}' % queue_id + "'"

    elif mode == 'del':
        #print './qospath2.py -d -N "%s" -c %s' % (name,controller_ip)
        os.system('./qospath2.py -d -N "%s" -c %s' % (name_fw,controller_ip))
        #print './qospath2.py -d -N "%s" -c %s' % (name,controller_ip)
        os.system('./qospath2.py -d -N "%s" -c %s' % (name_bw,controller_ip))

