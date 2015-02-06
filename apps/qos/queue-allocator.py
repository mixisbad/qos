#! /usr/bin/python
#  coding: utf-8

import sys
import io
import json
import Queue
import urllib

nodes = []
server_nodes = []
switch_nodes = []
server = {}
switches = {}
switches_dpid = {}
adjacent = []


existing_rules = {}

max_column = 0

#indicate max bandwidth on each link
speed = []
max_bandwidth = 10

#linkbandwidth = 10.0
traffic_file_name = "/home/mininet/floodlight-qos-beta-master/traffic.txt"
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

    page = urllib.urlopen('http://localhost:8080/wm/core/controller/switches/json')
    line = page.read().decode("utf-8")

    collections = json.loads(line)

    switchnum = len(collections)
    
    for sw in collections:
        dpid = sw["dpid"]
        port_detail = {}
        ports = sw["ports"]
        for each_port in ports:
            port_detail[each_port["portNumber"]] = each_port["name"]
        name_index[dpid] = port_detail
        

def measure_bandwidth():
    global traffic_data
    global traffic_file_name
    global name_index
    global f_ptr 
    global bandwidthout
    global switchnum

    page = urllib.urlopen('http://localhost:8080/wm/core/switch/all/flow/json')
    
    line = page.read().decode("utf-8")

    f_ptr = io.open(traffic_file_name,'w',encoding='utf-8')
    new_traffic_data = {}

    tmp_count_flow = [[] for i in range( len(adjacent))]
    for i in range( len(tmp_count_flow)):
        tmp_count_flow[i] = [[] for j in range( len(adjacent[i]) )]
        for j in range ( len( tmp_count_flow[i]) ):
            tmp_count_flow[i][j] = [0 for k in range( len(server_nodes))]


    switch_dicts = json.loads(line)
    for switch_id in switch_dicts:
        if switch_id in name_index:

            switch_index = nodes.index(switches[switch_id])

            
            #print "sw : "
            #print switch_id
            #print tmp_count_flow
            #print server
            #print server_nodes
            #print nodes

            for flow in switch_dicts[switch_id]:
                match = flow["match"]
                key_match = match["networkDestination"]+match["networkSource"]
                actions = flow["actions"]


                for action in actions:
                    #in case it want to connect with controller, using NAT to connect outside topology
                    if int(action["port"]) > len(bandwidthout[switch_index]):
                        continue

                    if action["type"] == "OUTPUT" or action["type"] == "OPAQUE_ENQUEUE":
                        total_duration = 0
                        total_byte = 0
                        found = False
                        if (switch_id,action["port"]) in traffic_data:
                            temp_traffic = traffic_data[(switch_id,action["port"])]
                            if key_match in temp_traffic:
                                temp_flow = temp_traffic[key_match]
                                old_duration = temp_flow["duration"]
                                old_bytecount = temp_flow["byteCount"]
                                total_duration = (flow["durationSeconds"]+flow["durationNanoseconds"]/1000000000)-old_duration
                                if total_duration >= 0:
                                    found = True
                                    total_byte = flow["byteCount"]-old_bytecount                            
                        if not found:
                            total_duration = (flow["durationSeconds"]+flow["durationNanoseconds"]/1000000000)
                            total_byte = flow["byteCount"]

                        buildkey = (switch_id,action["port"])
                        
                        #add information into globall traffic data for next iteration 
                        if buildkey not in new_traffic_data:
                            new_traffic_data[buildkey] = {}

                        #instead of using the whole match use only src,dst will be fine for this testing
                        new_traffic_data[buildkey][key_match] = {}
                        new_traffic_data[buildkey][key_match]["duration"] = (flow["durationSeconds"]+flow["durationNanoseconds"]/1000000000)
                        new_traffic_data[buildkey][key_match]["byteCount"] = flow["byteCount"]
                        
                        if total_duration > 0:
                            bw = ((total_byte*8)/(total_duration))/1000000
                        else:
                            bw = 0
                        #print "raw sw : " + switch_id
                        #print "sw id : " + str(switch_index)
                        #print "raw port : " + str(action["port"])
                        #print "port : " + str(int(action["port"])-1)
                        #print bandwidthout[switch_index]
                        bandwidthout[switch_index][int(action["port"])-1][0] = bandwidthout[switch_index][int(action["port"])-1][0] - bw

                        destination = match["networkDestination"]
                        source = match["networkSource"]
                        #print "destination : " + destination 
                        if destination in server:
                            #server_name = server[destination]['name']
                            #server_index = server_nodes.index(server_name)+1

                            #add 1 because bandwidth out want to reserve [0] for available bandwidth
                            server_index = server[destination]['id']+1
                            #print "server index : " + str(server_index)
                            bandwidthout[switch_index][int(action["port"])-1][server_index] = bandwidthout[switch_index][int(action["port"])-1][server_index] + bw
                            #print tmp_count_flow[switch_index]
                            # subtract 1 because use 0 base to count
                            tmp_count_flow[switch_index][int(action["port"])-1][server_index-1] = tmp_count_flow[switch_index][int(action["port"])-1][server_index-1] + 1
                            print adjacent
                            #check if it is the src node
                            server_name = server[destination]['name']
                            server_nodes_index = nodes.index(server_name)
                            if server_nodes_index in adjacent[switch_index]:
                                #need to be stored. So we can track along the path and see the minimum one
                                rules_name = source+"-"+destination
                            
                        elif source in server:
                            server_index = server[source]['id']+1
                            #print "server index : " + str(server_index)
                            bandwidthout[switch_index][int(action["port"])-1][server_index] = bandwidthout[switch_index][int(action["port"])-1][server_index] + bw
                            #print tmp_count_flow[switch_index]
                            # subtract 1 because use 0 base to count
                            tmp_count_flow[switch_index][int(action["port"])-1][server_index-1] = tmp_count_flow[switch_index][int(action["port"])-1][server_index-1] + 1
                            
                            
    print tmp_count_flow
                            #print "after count"
                            

    #previously write number of switches and assume they all have less/equal than maxport
    f_ptr.write( unicode(str(len(switches)) + "\n"))


    #need to change into a list of how many switches and how many port each switch has

    #if switch_id in name_index:
    #switch_index = nodes.index(switches[switch_id])
    for key in name_index:
        f_ptr.write(key + "\n" + str(nodes.index( switches[key] )) +"\n")

    #print bandwidthout

    for sw in bandwidthout:
        f_ptr.write( unicode(str(len(sw)) + " "))
        for port in sw :
            f_ptr.write(unicode( str( port[0] if port[0] >= 0 else 0)  + " "))
        f_ptr.write(u"\n")
    #print("-----------------------------------------------------")
    f_ptr.closed
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
    #assume all the bandwidth available in every link is 3000000 for now
    index = 0
    #loop through all switches
    for focus_switch in adjacent:
        #loop through all output port of a switch to set queues
        focus_dpid = switches_dpid[switch_nodes[index]]
        print switch_nodes[index] + " : " + focus_dpid
        port_num = 0        
        for outport in focus_switch:
            #if output port is another switch, begin to check available bandwidth for each server from this output port
            if outport != -1 and outport < len(switch_nodes):

                node_avai_bandw = [-1 for i in range(len(nodes))]
                node_visited = [False for i in range(len(nodes))]

                ban_node = index
                 
                #start using modified Dijkstra for bottle neck and 
                #mark that don't come back to the switch whose outport itself which has the ref number as index
                #this queue is suppose to contains only switch
                process_queue = Queue.PriorityQueue()

                #add a start node
                #need to get from actual bandwidth map, node -> outport
                bandwidth = get_avai_bandwidth_on_link(index,port_num)
                node_avai_bandw[outport] = bandwidth

                #use max_bandwidth - bandwidth to be able to sort with priority queue
                process_queue.put( (max_bandwidth - bandwidth, outport) )
                node_visited[outport] = True
                #start a modified Dijkstra
                while not process_queue.empty():
                    item = process_queue.get()
                    node_id = item[1]
                     
                    #looking for available outgoing from the node
                    ports = adjacent[node_id]
                    count_port = 0
                    for next_node in ports:
                        if next_node == -1:
                            count_port = count_port+1
                            continue
                        #if next node is not a ban node and isn't visited yet
                        elif next_node != ban_node and not node_visited[next_node]:
                            #need to get from actual bandwidth map, node -> outport
                            bandwidth = get_avai_bandwidth_on_link(node_id,count_port)
                            bandwidth = min(bandwidth, node_avai_bandw[node_id])
                            node_avai_bandw[next_node] = bandwidth
                            node_visited[next_node] = True
                            #if next node is a switch then add to queue for further processing
                            if next_node < len(switch_nodes):
                                process_queue.put( (max_bandwidth - bandwidth, next_node) )
                            count_port = count_port + 1
                        else:
                            count_port = count_port + 1

                #after get all the results of each server 
                #need to consider to existing flows to the server that pass through the focusing port as well


                #show the result
                

                print name_index[focus_dpid][port_num+1]
                for i in range(len(switch_nodes),len(switch_nodes)+len(server_nodes)):
                    if node_visited[i]:
                        print nodes[i] + " : avai bw " + str(node_avai_bandw[i]) + " : existing bw " + str(get_exists_bandwidth_on_link(index,port_num, (i - len(switch_nodes)) ))

                #print "total bandwidth for " + nodes[index] + "-eth" + str(port_num+1) + " : " + str(total_bandwidth)

                #calculate total bandwidth
                #total_bandwidth = 0
                #for i in range(len(switch_nodes),len(switch_nodes)+len(server_nodes)):
                #    if node_visited[i]:
                #        print nodes[i] + " : bw " + str(node_avai_bandw[i])
                #        total_bandwidth = total_bandwidth + node_avai_bandw[i]
                #print "total bandwidth for " + nodes[index] + "-eth" + str(port_num+1) + " : " + str(total_bandwidth)

            port_num = port_num + 1
        index = index + 1

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
    #initial banwidthouy
    for i in range( len(bandwidthout) ):
        bw_row = bandwidthout[i]
        for j in range( len(bw_row) ):
            bw_row[j][0] = speed[i][j]
            for k in range ( 1, len(server_nodes)+1):
                bw_row[j][k] = 0

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
            server_nodes.append(item[0])
            

        #found switch
        elif ":" in item[1]:
            switch_nodes.append(item[0])
            switches[item[1]] = item[0]
            switches_dpid[item[0]] = item[1]

        line = topo_detail.readline()
        item = line.split()

    nodes = switch_nodes + server_nodes
        

    
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
            speed_row.append(float(item_info[1]))
        adjacent[nodes.index( switches[item[0]] )] = row
        speed[nodes.index(switches[item[0]])] = speed_row

        if len(row) > max_column:
            max_column = len(row)

        line = topo_detail.readline()
        item = line.split()

    print adjacent

    
#    for speed_row in speed:
#        for speed_detail in speed_row:
#            print speed_detail + " "
#        print "\n"

     

    allocate_bandwidthout()

    #begin the loop

    reset_bandwidthout()

    display_bandwidthout()
    
    measure_bandwidth()

    #call method to allocate queue on switch periodically
    #it already has a map so it just has to get bandwidth information from polling
    #assume all the bandwidth available in every link is 3000000 for now
    #need to merge this code and polling.py together
            
    #allocate_queue()
    
    #end the loop
