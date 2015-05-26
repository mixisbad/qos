#! /usr/bin/python
#  coding: utf-8

import sys
import io
import tempfile
import os
import time
import json
import Queue
import urllib
import urllib2
import contextlib

nodes = []
server_nodes = []
switch_nodes = []
server = {}
server_priority = []
switches = {}
switches_dpid = {}
adjacent = []

queue_property = []

existing_rules = {}

max_column = 0

#indicate max bandwidth on each link
speed = []
max_bandwidth = 10

#linkbandwidth = 10.0
traffic_file_name = "/home/mininet/floodlight-qos-beta-master/traffic.txt"
traffic_tmp_file_name = "/home/mininet/floodlight-qos-beta-master/traffic.txt.tmp"
traffic_bak_file_name = "/home/mininet/floodlight-qos-beta-master/traffic.txt.bak"
switchnum = 0
traffic_data = {}
name_index = {}
bandwidthout = [[]]
f_ptr = 0

flow_map = {}

#dummy data for test
#poll_map = [
#[3000000, 3000000, 3000000, 3000000, 3000000], 
#[3000000, 3000000, 3000000, 3000000, 3000000], 
#[3000000, 3000000, 3000000, 3000000, 3000000], 
#[3000000, 3000000, 3000000, 3000000, 3000000], 
#[3000000, 3000000, 3000000, 3000000]]

def build_port_name():
    global name_index

    #page = urllib.urlopen('http://localhost:8080/wm/core/controller/switches/json')

    with contextlib.closing(urllib2.urlopen('http://localhost:8080/wm/core/controller/switches/json')) as page:
        line = page.read().decode("utf-8")

    #line = page.read().decode("utf-8")

    collections = json.loads(line)

    switchnum = len(collections)
    
    for sw in collections:
        dpid = sw["dpid"]
        port_detail = {}
        ports = sw["ports"]
        for each_port in ports:
            port_detail[each_port["portNumber"]] = each_port["name"]
        name_index[dpid] = port_detail

    #print name_index

def measure_bandwidth():
    global traffic_data
    global traffic_file_name
    global name_index
    global f_ptr 
    global bandwidthout
    global switchnum

    #page = urllib.urlopen('http://localhost:8080/wm/core/switch/all/flow/json')

    

    with contextlib.closing(urllib2.urlopen('http://localhost:8080/wm/core/switch/all/flow/json')) as page:
        line = page.read().decode("utf-8")

        #line = page.read().decode("utf-8")

        new_traffic_data = {}
    
    

        #create tmp count flow (has row equal to number of switch)
        tmp_count_flow = [[] for i in range( len(adjacent))]
        for i in range( len(tmp_count_flow)):
            #each switch has column equal to number of its port
            tmp_count_flow[i] = [[] for j in range( len(adjacent[i]) )]
            #each port has number of counter equal to number of queue (number of server)
            for j in range ( len( tmp_count_flow[i]) ):
                tmp_count_flow[i][j] = [0 for k in range( len(server_nodes) )]

        rule_max_bw = {}
        existing_rules = [[] for i in range( len(switches) )]

        switch_dicts = json.loads(line)
        for switch_id in switch_dicts:
            if switch_id in name_index:

                switch_index = nodes.index(switches[switch_id])

                rule_update = [[] for i in range(len(adjacent[switch_index]))]
                for i in range( len(rule_update) ):
                    rule_update[i] = [[] for j in range( len(server_nodes) )]


                for flow in switch_dicts[switch_id]:
                    match = flow["match"]
                    key_match = match["networkDestination"]+match["networkSource"]
                    actions = flow["actions"]

                    
                    for action in actions:
                        port_int = int(action["port"])
                        #in case it want to connect with controller, using NAT to connect outside topology
                        if port_int > len(bandwidthout[switch_index]):
                            continue

                        if action["type"] == "OUTPUT" or action["type"] == "OPAQUE_ENQUEUE":
                            total_duration = 0
                            total_byte = 0
                            found = False

                            buildkey = (switch_id,port_int)

                            if buildkey in traffic_data:
                                temp_traffic = traffic_data[buildkey]
                                if key_match in temp_traffic:
                                    temp_flow = temp_traffic[key_match]
                                    old_duration = temp_flow["duration"]
                                    old_bytecount = temp_flow["byteCount"]
                                    total_duration = (flow["durationSeconds"]+flow["durationNanoseconds"]/1000000000.0)-old_duration                                    
                                    if total_duration >= 0:
                                        found = True
                                        total_byte = flow["byteCount"]-old_bytecount                            
                            if not found:
                                total_duration = (flow["durationSeconds"]+flow["durationNanoseconds"]/1000000000.0)
                                total_byte = flow["byteCount"]

                           
                            if buildkey not in new_traffic_data:
                                new_traffic_data[buildkey] = {}

                            #instead of using the whole match use only src,dst will be fine for this testing
                            new_traffic_data[buildkey][key_match] = {}
                            new_traffic_data[buildkey][key_match]["duration"] = (flow["durationSeconds"]+flow["durationNanoseconds"]/1000000000.0)
                            new_traffic_data[buildkey][key_match]["byteCount"] = flow["byteCount"]

                            bw = 0.0
                            if total_duration > 0:
                                bw = ((total_byte*8.0/1000000.0)/(total_duration))
                            else:
                                bw = 0.0
                            #print "raw sw : " + switch_id
                            #print "sw id : " + str(switch_index)
                            #print "raw port : " + str(action["port"])
                            #print "port : " + str(int(action["port"])-1)
                            '''
                            print "****************************"
                            print "bytecount"
                            print flow["byteCount"]
                            print "duration"
                            print flow["durationSeconds"]
                            print "total_byte"
                            print total_byte
                            print "total_duration"
                            print total_duration
                            print "bw"
                            print bw
                            print "****************************"
                            '''
                            bandwidthout[switch_index][port_int-1][0] = bandwidthout[switch_index][port_int-1][0] - bw
                  
                            destination = match["networkDestination"]
                            source = match["networkSource"]
                            #print "destination : " + destination 
                            if destination in server:
                                #server_name = server[destination]['name']
                                #server_index = server_nodes.index(server_name)+1


                                server_index = server[destination]['id']
                                #add 1 to server index because [0] is reserved for available
                                bandwidthout[switch_index][port_int-1][server_index+1] = bandwidthout[switch_index][port_int-1][server_index+1] + bw
                                #print tmp_count_flow[switch_index]

                                if action["type"] == "OPAQUE_ENQUEUE" :
                                    tmp_count_flow[switch_index][port_int-1][server_index] = tmp_count_flow[switch_index][port_int-1][server_index] + 1

                                #print adjacent
                                #check if it is the src node
                                server_name = server[destination]['name']
                                server_nodes_index = nodes.index(server_name)
                            
                                #generate rules name to mark for update in its port after finish all flow in a switch
                                rule_name = source+"-"+destination
                                rule_update[port_int-1][server_index].append(rule_name)
                            
                            elif source in server:
                                server_index = server[source]['id']


                                bandwidthout[switch_index][port_int-1][server_index+1] = bandwidthout[switch_index][port_int-1][server_index+1] + bw
                                #print tmp_count_flow[switch_index]

                                if action["type"] == "OPAQUE_ENQUEUE" :
                                    tmp_count_flow[switch_index][port_int-1][server_index] = tmp_count_flow[switch_index][port_int-1][server_index] + 1

                                server_name = server[source]['name']
                                server_nodes_index = nodes.index(server_name)
                            
                                #print "port : " + str(port_int)
                                #generate rules name to mark for update in its port after finish all flow in a switch
                                rule_name = source+"-"+destination
                                #print "rule name : " + rule_name
                                rule_update[port_int-1][server_index].append(rule_name)
                        #endif action = output / opaque queue
                    #endloop each action
                #endloop each flow
                
                #print rule_update
                #begin count and show associate rule with this port
                #print "sw : " + str(switch_index+1)

                #loop i for all port in switch
                for i in range( len(adjacent[switch_index]) ):
                    #print "port : " + str( i+1 )
                    tmp_cal = [0 for j in range( len(tmp_count_flow[switch_index][i]) )]
                    total_momentum = 0

                    #loop j for all queue (#server) in a port
                    for j in range( len(tmp_count_flow[switch_index][i]) ):
                        flow = tmp_count_flow[switch_index][i][j]
                        #print "count : " + str(flow)
                        momentum = flow*server_priority[j]
                        tmp_cal[j] = momentum
                        #print "momentum : " + str(momentum)
                        total_momentum = total_momentum + momentum

                    #print "total momentum : " + str(total_momentum)

                    #loop j for all queue in a port
                    for j in range( len(tmp_cal) ):
                        if total_momentum > 0:
                            # 0 is an index for min bandwidth
                            queue_property[switch_index][i][j][0] = (tmp_cal[j] * speed[switch_index][i]) / total_momentum
                            #try set for max
                            #queue_property[switch_index][i][j][1] = (tmp_cal[j] * speed[switch_index][i]) / total_momentum
                            if queue_property[switch_index][i][j][1] < speed[switch_index][i]/20.0 :
                                queue_property[switch_index][i][j][1] = speed[switch_index][i]/20.0
                        else:
                            #queue_property[switch_index][i][j][0] = 0.0
                            queue_property[switch_index][i][j][1] = speed[switch_index][i]/20.0
                            #try set for max
                            #queue_property[switch_index][i][j][1] = speed[switch_index][i]

                        queue_property[switch_index][i][j][1] = speed[switch_index][i]
                        #try set for min
                        #queue_property[switch_index][i][j][0] = queue_property[switch_index][i][j][1]
                        
                        #try set both bound
                        #need to check for update the max bandwidth for the rule 
                    
                        for each_rule in rule_update[i][j]:
                            if each_rule in rule_max_bw:
                                if rule_max_bw[each_rule] < queue_property[switch_index][i][j][0]:
                                    rule_max_bw[each_rule] = queue_property[switch_index][i][j][0]
                            else:
                                rule_max_bw[each_rule] = queue_property[switch_index][i][j][0]
                            

                        # 1 is an index for max bandwidth
                        #queue_property[switch_index][i][j][1] = speed[switch_index][i]
                        #try set for both bound

                        #print "queue : " + str(j) + " min : " + str(queue_property[switch_index][i][j][0]) + " max : " + str(queue_property[switch_index][i][j][1])
                #endloop each port in switch
                #for rule_name in existing_rules:
    
                #print tmp_count_flow
                #print "after count"
                existing_rules[switch_index] = rule_update
            #endif known switch
        
        #endloop each switch                            

        #print queue_property

        #need to determine max bandwidth by the max ratio found in the path
        #for switch_row in range( len(queue_property) ):
        #    for port_row in range( len( queue_property[switch_row] ) ):
        #        for queue_row in range( len( queue_property[switch_row][port_row]) ):

        for switch_row in range( len(existing_rules) ):
            for port_row in range( len( existing_rules[switch_row] ) ):
                for queue_row in range( len( existing_rules[switch_row][port_row]) ):
                    #get a list that contain every rule name on that queue( in the focusing port )
                    rule_port_dict = existing_rules[switch_row][port_row][queue_row]
                
                    #begin to find the max out of the existing rule in this queue
                    tmp_max = 0
                    for rule_focus_name in rule_port_dict:
                        if tmp_max < rule_max_bw[rule_focus_name]:
                            tmp_max = rule_max_bw[rule_focus_name]

                    #get the max ratio of all the path
                    if queue_property[switch_row][port_row][queue_row][1] > tmp_max:
                        queue_property[switch_row][port_row][queue_row][1] = tmp_max

            
        
        #print rule_max_bw
        #print "---------------------------------"
        #print existing_rules
        
        #dirname, basename = os.path.split(traffic_file_name)
        #f_ptr = tempfile.NamedTemporaryFile(prefix=basename, dir=dirname)
        #print f_ptr.name

        f_ptr = io.open(traffic_tmp_file_name,'w',encoding='utf-8')

        #previously write number of switches and assume they all have less/equal than maxport
        f_ptr.write( unicode(str(len(switches)) + "\n"))
        f_ptr.flush()

        #need to change into a list of how many switches and how many port each switch has

        for key in switches:
            f_ptr.write(key + "\n" + unicode(str(nodes.index( switches[key] ))) +"\n")
            f_ptr.flush()

        #print bandwidthout

        for sw in bandwidthout:
            f_ptr.write( unicode(str(len(sw)) + " "))
            for port in sw :
                f_ptr.write(unicode( str( port[0] if port[0] >= 0 else 0)  + " "))
            f_ptr.write(u"\n")
            f_ptr.flush()
        #print("-----------------------------------------------------")
        os.fsync(f_ptr.fileno())
        f_ptr.closed
        os.rename(traffic_file_name, traffic_bak_file_name)
        #print "successfully rename current file to tmp file"
        os.rename(traffic_tmp_file_name , traffic_file_name)
        #print "successfully rename tmp file to current file"
        os.remove(traffic_bak_file_name)
        #print "successfully remove bak file"

        traffic_data = new_traffic_data
                        

#get available bandwidth
def get_avai_bandwidth_on_link(switch,outport):
    sw = bandwidthout[switch]
    bandwidth = sw[outport][0]
    return bandwidth

#switch ,outport, server are 0 based
def get_exists_bandwidth_on_link(switch,outport,server):
    server_index = server+1
    bw = bandwidthout[switch][outport][server_index]
    return bw

def allocate_queue():
    #begin loop to look all switch
    #print "allocate queue get called here"
    for index in range(0, len(queue_property) ):
        focus_dpid = switches_dpid[switch_nodes[index]]
        #print switch_nodes[index] + " : " + focus_dpid
        #begin loop to look all port
        for port_num in range(0, len(queue_property[index]) ):
            if focus_dpid in name_index:
                #print "allocate queue get called here"
                port = name_index[focus_dpid][port_num+1]
                qosmax = speed[index][port_num]

                queuecmd = "sudo ovs-vsctl -- set port %s qos=@qosport%s -- " % ( port , port )
                queuecmd = queuecmd + "--id=@qosport%s create qos type=linux-htb other-config:max-rate=%d " % ( port , int(qosmax) )
                queuecmd = queuecmd + "queues=0=@q0"
                for i in range(1, len(queue_property[index][port_num])+1):
                    queuecmd = queuecmd + "," + str(i) + "=@q" + str(i)

                queuecmd = queuecmd + " -- "
                queuecmd = queuecmd +     "--id=@q0 create queue other-config:max-rate=%d other-config:min-rate=%s " % ( int(qosmax) , "0" )
                for i in range(1, len(queue_property[index][port_num])+1):
                    queuecmd = queuecmd + "-- --id=@q%s create queue other-config:max-rate=%s other-config:min-rate=%s " %( str(i), str(queue_property[index][port_num][i-1][1]), str(queue_property[index][port_num][i-1][0]) )
                    #queuecmd = queuecmd + "-- --id=@q%s create queue other-config:max-rate=%s other-config:min-rate=%s " %( str(i), int(queue_property[index][port_num][i-1][0]), int(queue_property[index][port_num][i-1][0]) )



            
                print "result : \n\n "		
                print queuecmd
                print os.popen(queuecmd).read()
                #os.popen(queuecmd)
                #print "end result : \n\n "

def allocate_bandwidthout():
    global bandwidthout
    global adjacent

    #initial banwidthout
    bandwidthout = []
    for adj_row in adjacent:
        bw_row = [[] for i in range( len(adj_row)) ]
        for i in range( len(bw_row) ):
            bw_row[i] = [[] for j in range( len(server_nodes)+1 ) ]
        bandwidthout.append(bw_row)

def reset_bandwidthout():
    global bandwidthout
    global speed
    #initial bandwidthout
    for i in range( len(bandwidthout) ):
        bw_row = bandwidthout[i]
        for j in range( len(bw_row) ):
            bw_row[j][0] = speed[i][j]/1000000.0
            for k in range ( 1, len(server_nodes)+1):
                bw_row[j][k] = 0

    #print bandwidthout

def display_bandwidthout():
    global bandwidthout
    #initial banwidthouy
    for i in range( len(bandwidthout) ):
        bw_row = bandwidthout[i]
        for j in range( len(bw_row) ):
            print str(bw_row[j]) + " "
        print "\n"


if __name__ == '__main__':
    #global nodes
    #global server_nodes
    #global switch_nodes
    #global switches
    #global servers
    #global adjacent
    #global speed
    #global bandwidthout
    #global max_bandwidth

    build_port_name()

    topo_detail = open('topology_detail.txt','r')
    
    line = topo_detail.readline()
    item = line.split()


    #start mapping nodes
    while len(item) == 0 or item[0] != 'node':
        line = topo_detail.readline()
        item = line.split()


    line = topo_detail.readline()
    item = line.split()
    while len(item) > 0:

        #found server
        if "." in item[1]:
            server[item[1]] = {}
            server[item[1]]['name'] = item[0]
            server[item[1]]['id'] = len(server_nodes)
            server[item[1]]['queue'] = int(item[2])
            server_priority.append( float(item[3]) )
            #server[item[1]]['priority'] = int(item[2])
            server_nodes.append(item[0])
            

        #found switch
        elif ":" in item[1]:
            switch_nodes.append(item[0])
            switches[item[1]] = item[0]
            switches_dpid[item[0]] = item[1]

        line = topo_detail.readline()
        item = line.split()

    nodes = switch_nodes + server_nodes
        
    #print server
    
    #start building adjacent matrix 
    #adjacent information on tology_detail.txt contains only switches' adjacent information
    #row of adjacent equal to number of switch

    line = topo_detail.readline()
    item = line.split()
    while len(item) == 0 or item[0] != 'adjacent':
        line = topo_detail.readline()
        item = line.split()

    adjacent = [[] for i in range( len(switch_nodes) )]

    speed = [[] for i in range( len(switch_nodes) )]

    queue_property = [[] for i in range( len(switch_nodes) )]
    


    line = topo_detail.readline()
    item = line.split()
    while len(item) > 0:
        row = []
        speed_row = []
        item_info = []
        for i in range(1,len(item)):
            item_info = item[i].split(',')
            if item_info[0] in nodes:
                row.append( nodes.index(item_info[0]) )
            else:
                row.append( -1 )
            speed_row.append(float(item_info[1])*1000000.0)
            
        switch_index = nodes.index( switches[item[0]] )
        adjacent[switch_index] = row
        speed[switch_index] = speed_row
        
        queue_property[switch_index] = [ [] for i in range( len(row) )]
        for i in range( len( queue_property[switch_index]) ):
            queue_property[switch_index][i] = [ [] for j in range( len(server) )]
            
            for j in range( len(server) ):
                queue_property[switch_index][i][j] = [0,0]

        #if len(row) > max_column:
        #    max_column = len(row)

        line = topo_detail.readline()
        item = line.split()

    topo_detail.close()
    #print adjacent

    
#    for speed_row in speed:
#        for speed_detail in speed_row:
#            print speed_detail + " "
#        print "\n"

     

    allocate_bandwidthout()

    #begin the loop
    
    #while True :
    #for t in range(1):
    reset_bandwidthout()
    time.sleep(3)

    #call method to allocate queue on switch periodically
    #it already has a map so it just has to get bandwidth information from polling
    measure_bandwidth()

    allocate_queue()
            
    
    #end the loop
