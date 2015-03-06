#! /usr/bin/python
"""
circuitpusher utilizes floodlight rest APIs to create a bidirectional circuit, 
i.e., permanent flow entry, on all switches in route between two devices based 
on IP addresses with specified priority.
 
Notes:
 1. The circuit pusher currently only creates circuit with two IP end points 
 2. Prior to sending restAPI requests to the circuit pusher, the specified end
    points must already been known to the controller (i.e., already have sent
    packets on the network, easy way to assure this is to do a ping (to any
    target) from the two hosts.
 3. The current supported command syntax format is:
    a) circuitpusher.py --controller={IP}:{rest port} --type ip --src {IP} --dst {IP} --add --name {circuit-name}
 
       adds a new circuit between src and dst devices Currently ip circuit is supported. ARP is automatically supported.
    
       Currently a simple circuit record storage is provided in a text file circuits.json in the working directory.
       The file is not protected and does not clean itself between controller restarts.  The file is needed for correct operation
       and the user should make sure deleting the file when floodlight controller is restarted.

    b) circuitpusher.py --controller={IP}:{rest port} --delete --name {circuit-name}

       deletes a created circuit (as recorded in circuits.json) using the previously given name

@author kcwang
"""

import os
import sys
import subprocess
import json
import argparse
import io
import time
from datetime import datetime
import urllib
import urllib2
import mysql.connector

# parse circuit options.  Currently supports add and delete actions.
# Syntax:
#   circuitpusher --controller {IP:REST_PORT} --add --name {CIRCUIT_NAME} --type ip --src {IP} --dst {IP} 
#   circuitpusher --controller {IP:REST_PORT} --delete --name {CIRCUIT_NAME}

parser = argparse.ArgumentParser(description='Circuit Pusher')
parser.add_argument('--controller', dest='controllerRestIp', action='store', default='localhost:8080', help='controller IP:RESTport, e.g., localhost:8080 or A.B.C.D:8080')
parser.add_argument('--add', dest='action', action='store_const', const='add', default='add', help='action: add, delete')
parser.add_argument('--delete', dest='action', action='store_const', const='delete', default='add', help='action: add, delete')
parser.add_argument('--type', dest='type', action='store', default='ip', help='valid types: ip')
parser.add_argument('--src', dest='srcAddress', action='store', default='0.0.0.0', help='source address: if type=ip, A.B.C.D')
parser.add_argument('--dst', dest='dstAddress', action='store', default='0.0.0.0', help='destination address: if type=ip, A.B.C.D')
parser.add_argument('--name', dest='circuitName', action='store', default='circuit-1', help='name for circuit, e.g., circuit-1')

#user catches
if len(sys.argv) == 1:
 command = './circuitpusher.py -h'
 instruct = os.popen(command).read()
 print instruct
 exit(1)
elif sys.argv[1] == "help":
 command = './circuitpusher.py -h'
 instruct = os.popen(command).read()
 print instruct
 exit(1)

#parse arguments
args = parser.parse_args()
print args

controllerRestIp = args.controllerRestIp

# first check if a local file exists, which needs to be updated after add/delete
#if os.path.exists('./circuits.json'):
#    circuitDb = open('./circuits.json','r')
#    lines = circuitDb.readlines()
#    circuitDb.close()
#else:
#    lines={}

flag_exists_circuit = False;

cnx = mysql.connector.connect(user='thesis', password='password',
                              host='10.0.2.15',
                              database='thesis')

cursor = cnx.cursor()

query = "SELECT name FROM circuit WHERE name = '%s' " % args.circuitName

cursor.execute(query)
row = cursor.fetchone()

if row is not None:
    flag_exists_circuit = True
else:
    flag_exists_circuit = False

cnx.close()

if args.action=='add':

   

    #circuitDb = open('./circuits.json','a')
    
    if flag_exists_circuit:
        print "Circuit %s exists already. Use new name to create." % args.circuitName
        sys.exit()
    #else:
    #    circuitExists = False

    
    
    # retrieve source and destination device attachment points
    # using DeviceManager rest API 
    
    #command = "curl -s http://%s/wm/device/?ipv4=%s" % (args.controllerRestIp, args.srcAddress)
    myurl = "http://%s/wm/device/?ipv4=%s" % (args.controllerRestIp, args.srcAddress)
    #print command+"\n"
    #print myurl

    data = urllib2.urlopen(myurl)
    result = data.read()
    data.close()
    #result = os.popen(command).read()
    parsedResult = json.loads(result)

    sourceSwitch = parsedResult[0]['attachmentPoint'][0]['switchDPID']
    sourcePort = parsedResult[0]['attachmentPoint'][0]['port']
    
    #command = "curl -s http://%s/wm/device/?ipv4=%s" % (args.controllerRestIp, args.dstAddress)
    myurl = "http://%s/wm/device/?ipv4=%s" % (args.controllerRestIp, args.dstAddress)

    data = urllib2.urlopen(myurl)
    result = data.read()
    data.close()
    #result = os.popen(command).read()
    parsedResult = json.loads(result)
    #print command+"\n"
    destSwitch = parsedResult[0]['attachmentPoint'][0]['switchDPID']
    destPort = parsedResult[0]['attachmentPoint'][0]['port']
    
    print "Creating circuit:"
    print "from source device at switch %s port %s" % (sourceSwitch,sourcePort)
    print "to destination device at switch %s port %s"% (destSwitch,destPort)
    
    # retrieving route from source to destination
    # using Routing rest API
    
    #command = "curl -s http://%s/wm/topology/route/%s/%s/%s/%s/json" % (controllerRestIp, sourceSwitch, sourcePort, destSwitch, destPort)

    myurl = "http://%s/wm/topology/route/%s/%s/%s/%s/json" % (controllerRestIp, sourceSwitch, sourcePort, destSwitch, destPort)
    
    data = urllib2.urlopen(myurl)
    result = data.read()
    data.close()
    #result = os.popen(command).read()
    parsedResult = json.loads(result)

    #print myurl+"\n"
    #print result+"\n"

    cnx = mysql.connector.connect(user='thesis', password='password',host='10.0.2.15',database='thesis')

    cursor = cnx.cursor()

    for i in range(len(parsedResult)):
        if i % 2 == 0:
            ap1Dpid = parsedResult[i]['switch']
            ap1Port = parsedResult[i]['port']
            print ap1Dpid, ap1Port
            
        else:
            ap2Dpid = parsedResult[i]['switch']
            ap2Port = parsedResult[i]['port']
            print ap2Dpid, ap2Port
            

            # edit by pattanapoom change to store in DB
            # store created circuit attributes in local ./circuits.json
            #datetime = time.asctime()
            #circuitParams = {'name':args.circuitName, 'Dpid':ap1Dpid, 'inPort':ap1Port, 'outPort':ap2Port, 'datetime':datetime}
            #str_json = json.dumps(circuitParams)
            #circuitDb.write(str_json+"\n")

            
            query = "INSERT INTO circuit values('%s', '%s', %s, %s, '%s')" % (args.circuitName, ap1Dpid, ap1Port, ap2Port, datetime.now())
            #print '******************************************'
            #print query
            #print '******************************************'
            cursor.execute(query)

            #end edit by pattanapoom store results in DB



        
            
        
    cnx.commit()
    cnx.close()

    # confirm successful circuit creation
    # using controller rest API
    #command="curl -s http://%s/wm/core/switch/all/flow/json| python -mjson.tool" % (controllerRestIp)
    #result = os.popen(command).read()
    #print command + "\n" + result

    #circuitDb.close()

elif args.action=='delete':
    
    #circuitDb = open('./circuits.json','w')

    # removing previously created flow from switches
    # using StaticFlowPusher rest API       
    # currently, circuitpusher records created circuits in local file ./circuits.db 
    # with circuit name and list of switches                                  

    #circuitExists = False

    #for line in lines:
    #    data = json.loads(line)
    #    if data['name']==(args.circuitName):
    #        circuitExists = True
    #    else:
    #        circuitDb.write(line)

    #circuitDb.close()

    if flag_exists_circuit:

        cnx = mysql.connector.connect(user='thesis', password='password',host='10.0.2.15',database='thesis')

        cursor = cnx.cursor()
        query = "DELETE FROM circuit where name = '%s'" 
        cursor.execute(query,(args.circuitName))
        cnx.commit()
        cnx.close()

    else:
        print "specified circuit does not exist"
        #sys.exit()

